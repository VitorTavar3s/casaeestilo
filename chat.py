from mcp.client.streamable_http import streamable_http_client
from contextlib import AsyncExitStack
from mcp import ClientSession
from cache import *
from llm import *
import asyncio
import json


NOME_ESPECIALISTA = "Casa & Estilo"
BASE_CONHECIMENTO = "conhecimento/casa_estilo.json"
MODELO = "gemini-3.5-flash-lite"

CACHE = "cache"
MODELO_CACHE = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
NOME_CACHE = "casa_estilo_cache"

URL_FERRAMENTAS = "http://localhost:8000/mcp"


def iniciar_persona_assistente(conhecimento):
    persona = [
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    f"Você é um especialista em decoração de interiores chamado {NOME_ESPECIALISTA}. "
                    "Você ajuda o usuário a decorar ambientes considerando estilo pessoal, espaço disponível, "
                    "orçamento, iluminação, funcionalidade, móveis existentes e necessidades dos moradores."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Se o usuário fizer uma saudação, informe que você é um software, não um humano, "
                    "e que pode ajudar a planejar a decoração de ambientes."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Antes de elaborar uma proposta personalizada, verifique se você conhece pelo menos: "
                    "o tipo de ambiente, as dimensões ou a área, o estilo preferido, o orçamento disponível, "
                    "a iluminação natural e a finalidade do ambiente. "
                    "Se faltar alguma informação essencial, faça no máximo três perguntas curtas e objetivas."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Sempre que o usuário informar medidas, móveis, orçamento ou iluminação, "
                    "utilize as ferramentas disponíveis para analisar circulação, área útil, orçamento e iluminação "
                    "antes de formular a recomendação final."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "A resposta final deve conter: diagnóstico do ambiente, estilo recomendado, paleta de cores, "
                    "sugestões de móveis e organização, iluminação, itens prioritários, estimativa de custo e "
                    "possíveis adaptações para respeitar o orçamento."
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Se o usuário pedir algo fora do escopo de decoração, organização de ambientes, "
                    "iluminação, móveis, cores, materiais ou reformas leves, responda: "
                    "'Não posso responder esta pergunta. Posso ajudar com sugestões de decoração e organização de ambientes.'"
                )
            }]
        },
        {
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    "Não invente preços, medidas, disponibilidade de produtos ou marcas. "
                    "Quando não houver informação suficiente, explique a limitação e solicite o dado necessário."
                )
            }]
        }
    ]

    for mensagem, resposta in conhecimento:
        persona.append({
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": (
                    f"Caso o usuário fale ou pergunte '{mensagem}' ou algo parecido, "
                    f"sua resposta deve seguir esta orientação: '{resposta}'"
                )
            }]
        })

    return persona


async def carregar_conhecimento(base_conhecimento=BASE_CONHECIMENTO):
    carregado, conhecimento = False, []

    try:
        with open(base_conhecimento, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)

        for pergunta_resposta in conteudo:
            pergunta = pergunta_resposta["pergunta"]
            resposta = pergunta_resposta["resposta"]

            conhecimento.append((pergunta, resposta))

        carregado = True
    except Exception as e:
        print(f"erro carregando conhecimento: {e}")

    return carregado, conhecimento


async def conectar_ferramentas(contexto, url_ferramentas=URL_FERRAMENTAS):
    conexao_mcp, ferramentas = None, []

    try:
        stream_leitura, stream_escrita = await contexto.enter_async_context(
            streamable_http_client(url_ferramentas)
        )

        conexao_mcp = await contexto.enter_async_context(
            ClientSession(stream_leitura, stream_escrita)
        )

        await conexao_mcp.initialize()

        listagem_ferramentas = await conexao_mcp.list_tools()

        for ferramenta in listagem_ferramentas.tools:
            ferramentas.append({
                "type": "function",
                "name": ferramenta.name,
                "description": ferramenta.description,
                "parameters": ferramenta.input_schema
            })
    except Exception as e:
        print(f"erro conectando as ferramentas: {e}")

    return conexao_mcp, ferramentas


def extrair_texto_execucao(resultado):
    if resultado.structured_content:
        return json.dumps(resultado.structured_content, ensure_ascii=False)

    conteudo = []

    for conteudo_item in resultado.content:
        if hasattr(conteudo_item, "text"):
            conteudo.append(conteudo_item.text)
        else:
            conteudo.append(str(conteudo_item))

    return "\n".join(conteudo)


async def executar_ferramentas(conexao_mcp, resposta, mensagens):
    ferramentas_para_executar = [
        passo for passo in resposta.steps
        if passo.type == "function_call"
    ]

    if ferramentas_para_executar:
        for ferramenta in ferramentas_para_executar:
            execucao = await conexao_mcp.call_tool(
                ferramenta.name,
                arguments=ferramenta.arguments
            )

            mensagens.append({
                "type": "function_result",
                "name": ferramenta.name,
                "call_id": ferramenta.id,
                "result": [
                    {
                        "type": "text",
                        "text": extrair_texto_execucao(execucao)
                    }
                ]
            })

    return len(ferramentas_para_executar) > 0


async def executar():
    contexto = AsyncExitStack()

    conexao_mcp, ferramentas = await conectar_ferramentas(contexto)

    if not ferramentas:
        print("não foram encontradas ferramentas")
    else:
        for ferramenta in ferramentas:
            print(
                f"ferramenta encontrada: {ferramenta['name']}, "
                f"descrição: {ferramenta['description']}"
            )

    iniciado, llm = await iniciar_llm()

    if not iniciado:
        await contexto.aclose()
        print("erro iniciando llm")
        return

    carregado, conhecimento = await carregar_conhecimento()

    if not carregado:
        await contexto.aclose()
        print("erro carregando conhecimento")
        return

    iniciado, modelo_cache, colecao_cache = iniciar_cache(
        MODELO_CACHE,
        CACHE,
        NOME_CACHE
    )

    if not iniciado:
        await contexto.aclose()
        print("erro iniciando cache")
        return

    persona = iniciar_persona_assistente(conhecimento)

    while True:
        mensagem = input("👤 ")

        if mensagem in ["sair", "/s"]:
            await contexto.aclose()
            break

        persona.append({
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": mensagem
            }]
        })

        encontrada, resposta = buscar_cache(
            mensagem,
            modelo_cache,
            colecao_cache
        )

        if encontrada:
            persona.append({
                "type": "model_output",
                "text": resposta
            })

            print(f"🤖 {resposta} [resposta do cache]")
        else:
            ferramentas_executadas = False

            while True:
                sucesso, resposta = await obter_resposta(
                    llm,
                    persona,
                    ferramentas,
                    modelo=MODELO
                )

                persona.extend(resposta.steps)

                if sucesso:
                    print(f"🤖 tokens consumidos: {get_consumo_tokens(resposta)}")

                    if not await executar_ferramentas(
                        conexao_mcp,
                        resposta,
                        persona
                    ):
                        resposta = resposta.output_text
                        break

                    ferramentas_executadas = True

            print(f"🤖 {resposta} [resposta do llm]")

            if not ferramentas_executadas:
                gravar_cache(
                    mensagem,
                    resposta,
                    modelo_cache,
                    colecao_cache
                )

    await contexto.aclose()


if __name__ == "__main__":
    asyncio.run(executar())