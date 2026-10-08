# powerbi-pdf-completo

[![testes](https://github.com/BrunoMaia23/powerbi-pdf-completo/actions/workflows/testes.yml/badge.svg)](https://github.com/BrunoMaia23/powerbi-pdf-completo/actions/workflows/testes.yml)

Exportar uma página do Power BI para PDF parece simples até aparecer uma matriz com barra de rolagem:
o PDF sai só com as linhas que estavam visíveis na tela. No trabalho isso aconteceu num relatório de
valores por item, em que o extrato dos clientes maiores tinha muito mais linhas do que cabiam na
matriz. Este repositório mostra as duas saídas que montei para isso, refeitas sobre um modelo fictício
de extrato de comissões.

*In English: getting a complete PDF out of a Power BI report whose matrix hides rows behind a scrollbar.
DAX measures for a print-friendly page with an overflow warning, a paginated report (RDL) opened with the
current filters through a DAX-built URL, and a Python check that compares an exported PDF with the expected
query result. Synthetic data.*

## Saída 1: uma página feita para imprimir

Uma página alta, com os mesmos filtros da página original, em que o extrato aparece em várias tabelas
lado a lado. Cada tabela recebe um bloco contínuo do extrato, e quem decide em qual tabela cada item cai
é uma medida (`dax/medidas_pagina_pdf.dax`):

- `Linha no PDF` é a posição do item na ordem do extrato, contando só os itens que têm valor no filtro;
- `Tabela no PDF` reparte essas posições em blocos iguais. Cada tabela visual tem o filtro
  `[Tabela no PDF] = k`;
- `Aviso do PDF` aparece num card quando o filtro tem mais itens do que a página comporta.

A altura da página é fixa, então sempre existe um limite. A diferença é que agora, quando ele estoura,
o PDF diz isso em vermelho no topo, em vez de cortar linhas em silêncio.

## Saída 2: o PDF completo pelo relatório paginado

Para extrato de qualquer tamanho, um botão "PDF completo" abre o relatório paginado já filtrado e já
exportando em PDF. O relatório paginado quebra página sozinho, então não tem limite de linhas.

O botão usa uma URL montada por DAX (`dax/url_pdf_completo.dax`), com os filtros atuais como
parâmetros do relatório:

```
https://app.powerbi.com/groups/me/rdlreports/ID?rdl:format=PDF&rp:Ano=2025&rp:Vendedores=4&rp:Vendedores=13
```

Os filtros vão por ID, nunca por nome: número não precisa de escape na URL, e o DAX não tem função de
URL-encode. Sem filtro de vendedor vai o valor `TODOS`, que a consulta do paginado entende como "sem
filtro", porque a lista inteira de IDs estouraria o tamanho da URL. Uma segunda medida avisa quando a
URL passa de 1.800 caracteres.

O relatório paginado está em `rdl/extrato_completo.rdl`: uma consulta DAX com os parâmetros `@Ano` e
`@Vendedores`, a tabela agrupada por grupo de item com subtotal e total, os filtros no cabeçalho e
"Página x de y" no rodapé, em A4 e com números no formato brasileiro.

## Conferindo o PDF

Nos dois casos, a pergunta é a mesma: o PDF tem todos os itens do filtro, com os valores certos? Para
responder sem conferir na mão, rode a consulta do paginado (`dax/consulta_paginado.dax`) no DAX Studio
com o mesmo filtro, salve como CSV e compare:

```bash
pdfcompleto validar extrato.pdf esperado.csv
```

Com um PDF sintético no mesmo layout (o que os testes geram), para o vendedor 13 em 2025:

```
89 itens conferidos | faltando 0 | sobrando 0 | repetidos 0 | valor diferente 0
OK: o PDF tem todos os itens, com os valores certos.
```

A leitura não depende da ordem do texto. Nas tabelas lado a lado, a extração de texto do PDF mistura
as colunas numa mesma linha, então o validador procura cada ocorrência de "código, descrição, valor"
onde ela estiver.

## Rodando

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest

pdfcompleto dados --pasta modelo                     # CSVs do modelo fictício
pdfcompleto url --base https://app.powerbi.com/groups/me/rdlreports/ID --ano 2025 --vendedor 13
pdfcompleto distribuir --pasta modelo --ano 2025 --vendedor 13 --tabelas 4 --linhas-por-tabela 20
```

```
89 itens, 23 por tabela, 9 escondidos
O filtro tem 89 itens e a página mostra no máximo 80. Use o PDF completo (relatório paginado).
```

Os CSVs gerados servem para montar o modelo no Power BI Desktop: `fato_comissao` ligada a `dim_item`
por `codigo` e a `dim_vendedor` por `vendedor_id`.

## O que os testes cobrem, e o que não cobrem

O CI não roda DAX nem renderiza RDL, então os testes ficam no que dá para testar fora do Power BI:

- a URL montada em Python segue a mesma regra da medida DAX;
- a divisão entre tabelas espelha as medidas da página e conta as linhas que ficariam escondidas;
- o validador é testado contra PDFs gerados nos próprios testes com fpdf2, no layout de tabelas lado
  a lado, um completo e outro com uma linha faltando e um valor errado. Esses PDFs são sintéticos, não
  exportações do Power BI;
- o RDL é conferido por estrutura: os parâmetros chegam na consulta, os campos usados existem, a
  página é A4, e a consulta dentro do RDL é a mesma do arquivo `.dax`.

O RDL também passa no schema oficial 2016/01 da Microsoft. Esse schema não é distribuído aqui, mas vem
dentro do Power BI Report Builder (como recurso do `Microsoft.ReportingServices.ProcessingCore.dll`).
Com ele extraído, `RDL_XSD=caminho/do/schema.xsd pytest` valida o arquivo.

## Arquivos

```
dax/medidas_pagina_pdf.dax    medidas da página de impressão
dax/url_pdf_completo.dax      URL do botão "PDF completo"
dax/consulta_paginado.dax     consulta do relatório paginado
rdl/extrato_completo.rdl      relatório paginado
src/pdfcompleto/              dados fictícios, URL, divisão e validador
tests/
```
