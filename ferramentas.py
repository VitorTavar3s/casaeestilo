from mcp.server.mcpserver import MCPServer


NOME = "analisador_ambiente"
mcp = MCPServer(
    NOME,
    "ferramentas de análise para planejamento de decoração de ambientes"
)


@mcp.tool(
    name="calcular_area",
    title="Cálculo de área do ambiente",
    description=(
        "Calcula a área de um ambiente retangular a partir da largura e do comprimento em metros."
    )
)
def calcular_area(largura_m: float, comprimento_m: float):
    if largura_m <= 0 or comprimento_m <= 0:
        return {"erro": "As dimensões devem ser maiores que zero."}

    area = largura_m * comprimento_m

    return {
        "area_m2": round(area, 2),
        "classificacao": (
            "ambiente pequeno" if area < 10
            else "ambiente médio" if area < 20
            else "ambiente grande"
        )
    }


@mcp.tool(
    name="verificar_circulacao",
    title="Verificação de circulação e mobiliário",
    description=(
        "Verifica se há espaço mínimo de circulação entre um móvel e a parede oposta. "
        "Recomenda-se pelo menos 70 cm de passagem livre."
    )
)
def verificar_circulacao(largura_ambiente_m: float, largura_movel_m: float):
    if largura_ambiente_m <= 0 or largura_movel_m <= 0:
        return {"erro": "As dimensões devem ser maiores que zero."}

    circulacao = largura_ambiente_m - largura_movel_m

    return {
        "circulacao_m": round(circulacao, 2),
        "situacao": (
            "circulação adequada" if circulacao >= 0.70
            else "circulação apertada" if circulacao >= 0.50
            else "circulação insuficiente"
        ),
        "recomendacao": (
            "O móvel pode ser mantido na posição informada."
            if circulacao >= 0.70
            else "Considere um móvel menor, reposicionamento ou layout alternativo."
        )
    }


@mcp.tool(
    name="analisar_orcamento",
    title="Análise de orçamento",
    description=(
        "Soma os valores informados e compara o total com o orçamento disponível. "
        "Retorna o saldo, o percentual utilizado e uma classificação de viabilidade."
    )
)
def analisar_orcamento(orcamento_disponivel: float, itens: list[dict]):
    if orcamento_disponivel <= 0:
        return {"erro": "O orçamento deve ser maior que zero."}

    if not itens:
        return {"erro": "Informe pelo menos um item com nome e valor."}

    total = sum(
        float(item.get("valor", 0))
        for item in itens
    )
    saldo = orcamento_disponivel - total
    percentual = (total / orcamento_disponivel) * 100

    return {
        "orcamento_disponivel": round(orcamento_disponivel, 2),
        "total_estimado": round(total, 2),
        "saldo": round(saldo, 2),
        "percentual_utilizado": round(percentual, 2),
        "situacao": (
            "dentro do orçamento" if saldo >= 0
            else "orçamento excedido"
        ),
        "itens": itens
    }


@mcp.tool(
    name="recomendar_iluminacao",
    title="Recomendação de iluminação",
    description=(
        "Recomenda temperatura de cor, tipo de iluminação e potência aproximada "
        "para um ambiente, considerando área e nível de luz natural."
    )
)
def recomendar_iluminacao(
    ambiente: str,
    area_m2: float,
    luz_natural: str = "media"
):
    if area_m2 <= 0:
        return {"erro": "A área deve ser maior que zero."}

    temperatura_cor = {
        "quarto": "2700 K a 3000 K",
        "sala": "2700 K a 3000 K",
        "cozinha": "3000 K a 4000 K",
        "banheiro": "3000 K a 4000 K",
        "escritorio": "4000 K"
    }.get(ambiente.lower(), "3000 K")

    potencia_total_w = round(area_m2 * 7, 1)

    if luz_natural.lower() in ["baixa", "pouca", "escura"]:
        ajuste = "Priorize iluminação geral difusa, luminárias de parede e luz indireta."
    elif luz_natural.lower() in ["alta", "muita", "clara"]:
        ajuste = "Priorize controle de luz com cortinas e complemente com iluminação pontual."
    else:
        ajuste = "Combine luz geral, iluminação de tarefa e uma fonte de luz decorativa."

    return {
        "ambiente": ambiente,
        "area_m2": area_m2,
        "temperatura_cor_recomendada": temperatura_cor,
        "potencia_total_aproximada_w": potencia_total_w,
        "orientacao": ajuste
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        streamable_http_path="/mcp"
    )