# NetBox Topology VLAN

**Plugin para NetBox — Visualização Dinâmica e Automação de Topologias Lógicas de VLANs**

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)]()
[![NetBox](https://img.shields.io/badge/netbox-4.0%2B-3B7CBC)]()
[![Status](https://img.shields.io/badge/status-alpha-orange)]()

---

## Sobre o projeto

O [NetBox](https://github.com/netbox-community/netbox) é uma plataforma de referência para documentação de infraestruturas de rede, mas não oferece, de forma nativa, uma visualização da propagação lógica de VLANs entre equipamentos. Sem essa visão, diagnosticar uma falha de conectividade obriga a percorrer manualmente dispositivos, interfaces e cabos, um processo lento e sujeito a erro.

Este plugin resolve esse problema: a partir dos dados já registados no NetBox — dispositivos, interfaces, cabos e VLANs — gera automaticamente a topologia lógica de uma ou mais VLANs e apresenta-a numa interface gráfica interativa, com deteção de inconsistências, cálculo teórico de Spanning Tree e integração com o emulador GNS3.

Desenvolvido no âmbito do Projeto Final de Curso da Licenciatura em Engenharia Informática, Redes e Telecomunicações (LEIRT), ISEL.

## Índice

- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Utilização](#utilização)
- [API REST](#api-rest)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Limitações conhecidas](#limitações-conhecidas)
- [Trabalho futuro](#trabalho-futuro)
- [Informações académicas](#informações-académicas)
- [Referências](#referências)

## Funcionalidades

| Área | Descrição |
|---|---|
| **Geração automática de topologia** | Seleciona um *site* e uma ou mais VLANs; o plugin constrói o grafo lógico a partir de dispositivos, interfaces, cabos (`Cable`) e VLANs *tagged*/*untagged* já registados. |
| **Classificação Access/Trunk** | Interfaces com VLANs em `tagged_vlans` são tratadas como *Trunk*; as restantes como *Access*. Ligações *Trunk–Access* são assinaladas como possível inconsistência de configuração. |
| **Cálculo teórico de Spanning Tree** | Classe `STPCalculator`: elege a *root bridge* (critério IEEE 802.1D — prioridade + identificador), calcula custos de caminho via BFS e atribui papéis (*Root* / *Designated* / *Alternate*) e estados (*Forwarding* / *Blocking* / *Disabled*) de porta. Resultados escritos em *Custom Fields*, com gravação condicional. |
| **Execução assíncrona** | *Job* RQ (`CalculateSTPTopology`) recalcula STP para todas as VLANs em segundo plano; resultados em *cache* (TTL de 1 hora). |
| **Importação GNS3** | Lê ficheiros de projeto GNS3 e cria automaticamente *site*, dispositivos (Router / Switch / PC, mapeados a partir do `node_type`), interfaces e cabos no NetBox, dentro de uma transação atómica. |
| **Exportação** | Geração de PNG (captura do grafo), XML (estrutura de nós/ligações) e `.gns3` (reimportável no emulador). |
| **API REST** | Endpoints para topologia, VLANs por *site* e importação GNS3; suporte a múltiplas VLANs por pedido; filtros de pesquisa avançados. |
| **Interface interativa** | Renderização com [vis-network](https://visjs.github.io/vis-network/docs/network/); filtros por VLAN, tipo de dispositivo e estado STP; *popups* de detalhe; posições de nós persistidas (`DeviceCoordinates`); painel de estatísticas; atalhos de navegação. |
| **Cache invalidada por eventos** | *Signals* do Django invalidam a *cache* da topologia sempre que `Device`, `Interface` ou `VLAN` são criados, alterados ou eliminados. |

## Screenshots

### Dynamic VLAN Topology Visualization

![VLAN topology visualization](https://imgur.com/a/plugin-YBOIzg7)

Visualização interativa da topologia lógica de VLAN

### Dynamic VLAN Filtering

![VLAN filtering](https://i.imgur.com/r02B4iO.png)

Filtragem interativa da topologia por VLAN, permitindo destacar e visualizar VLANs específicas.

### Connection, VLAN and STP Details

![Connection, VLAN and STP details](https://i.imgur.com/y35Yvst.png)

Pop-ups interativos que exibem detalhes da conexão, VLANs transmitidas pelos links e estados das portas STP.

### Warnings

![Warnings 1](https://i.imgur.com/S99qYpD.png)
![Warnings 2](https://i.imgur.com/y9mP3aM.png)

### Network Topology Legend

![Network topology legend](https://i.imgur.com/7b58iMv.png)

Legenda visual que identifica dispositivos de rede, tipos de conexão e elementos de topologia representados no plugin.

## Requisitos

- **NetBox** ≥ 4.0 (depende de `from netbox.plugins import PluginConfig`). Testado com NetBox Community 4.6.4.
- **Python** ≥ 3.12
- **Worker RQ** ativo e *cache* configurada, para o cálculo assíncrono de STP
- Navegador moderno com JavaScript ativado

## Instalação

**1. Obter o código**

```bash
git clone https://github.com/Francisc0Lopes/Plugin-Netbox.git
pip install /caminho/para/Plugin-Netbox
```

**2. Registar o plugin** em `configuration.py`

```python
PLUGINS = [
    "netbox_topology_vlan"
]

# Opcional
PLUGINS_CONFIG = {
    "netbox_topology_vlan": {
        "enabled": True,
        "cache_timeout": 3600
    }
}
```

**3. Aplicar migrações e recolher ficheiros estáticos**

```bash
python manage.py migrate
python manage.py collectstatic
```

As migrações criam os *Custom Fields* de STP (`stp_priority`, `stp_root_bridge`, `stp_port_state`, `stp_port_role`).

**4. Reiniciar os serviços** e validar em `/plugins/topology-vlan/`.

## Utilização

1. Aceder ao menu **"Mapa de VLANs"** (ou ao botão de acesso rápido na página de detalhe de uma VLAN).
2. Selecionar o *site*.
3. Selecionar uma ou mais VLANs.
4. Gerar o grafo.
5. Consultar ligações via *popup*, aplicar filtros, reorganizar nós ou exportar (PNG / XML / GNS3).

Para representar informação STP no mapa, preencher os *Custom Fields* correspondentes — manualmente ou através do cálculo automático via *job* RQ.

## API REST

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/plugins/topology-vlan/get-site-vlans/` | `GET` | VLANs associadas a um *site* (registadas no *site* + em uso nas interfaces dos seus dispositivos) |
| `/api/plugins/topology-vlan/get-topology/` | `GET` | Topologia calculada para `vlan_id` (uma ou várias, separadas por vírgula) e, opcionalmente, `site_id` |
| `/api/plugins/topology-vlan/import-gns3/` | `POST` | Recebe um ficheiro de projeto GNS3 e cria a infraestrutura correspondente |

Resposta simplificada de `get-topology/`:

```json
{
  "vlan": {"id": 20, "vid": 20, "name": "PROD"},
  "nodes": [
    {"id": 1, "label": "SW-CORE-01", "type": "switch", "url": "/dcim/devices/1/"}
  ],
  "edges": [
    {
      "from": 1,
      "to": 2,
      "interface_a": "Gi0/1",
      "interface_b": "Gi0/24",
      "mode_a": "Trunk",
      "mode_b": "Access",
      "vlans_trunk": "10,20",
      "vlan_access": "20",
      "stp_state": "forwarding"
    }
  ]
}
```

### Filtros de consulta sobre VLANs

| Filtro | Campo | Comparação |
|---|---|---|
| `site_id` | `site.id` | Igualdade exata |
| `site_name` | `site.name` | Contém |
| `vid` | `vid` | Igualdade exata |
| `vid_range` | `vid` | Lista separada por vírgula |
| `status` | `status` | Igualdade exata |
| `role` | `role` | Contém |
| `name` | `name` | Contém |

O endpoint principal requer autenticação (`IsAuthenticated`).

## Estrutura do projeto

```text
netbox_topology_vlan/
├── __init__.py                       # Registo do plugin (PluginConfig)
├── navigation.py                     # Entrada "Mapa de VLANs" no menu
├── template_content.py               # Botão de acesso rápido nas páginas de VLAN
├── views.py / urls.py                # Rotas e views web
├── utils.py                          # Extração de dados e construção do grafo
├── stp_algorithm.py                  # Algoritmo de cálculo STP (STPCalculator)
├── jobs.py                           # Job assíncrono CalculateSTPTopology (RQ)
├── gns3_importer.py                  # Importação de projetos GNS3
├── signals.py                        # Invalidação de cache
├── models.py                         # Modelo DeviceCoordinates
├── filtersets.py                     # Filtros de pesquisa sobre VLANs
├── api/                              # Endpoints REST (views, urls, serializers)
├── migrations/                       # Modelo inicial e Custom Fields de STP
├── templates/netbox_topology_vlan/   # mapa.html, popup.html
└── static/netbox_topology_vlan/      # mapa.js (renderização do grafo)
```

> `middleware.py`, `graphql.py`, `tables.py` e `api/serializers.py` seguem o esqueleto padrão de um plugin NetBox e estão reservados para extensões futuras (GraphQL, tabelas nativas), sem implementação funcional na versão atual.

## Limitações conhecidas

- O estado STP é tratado como informação estática (manual ou teoricamente calculada), não como dado recolhido em tempo real dos equipamentos.
- Grafos com mais de ~500 nós tendem a degradar a performance de renderização no lado do cliente.

## Trabalho futuro

- Recolha automática de estado STP via SNMP, NETCONF, RESTCONF ou telemetria
- Suporte a GraphQL e tabelas nativas (`django-tables2`)
- Testes automatizados (`tests/`)

## Informações académicas

| | |
|---|---|
| **Instituição** | Instituto Superior de Engenharia de Lisboa (ISEL) |
| **Departamento** | Engenharia Eletrónica e Telecomunicações e de Computadores (DEETC) |
| **Curso** | Licenciatura em Engenharia Informática, Redes e Telecomunicações (LEIRT) |
| **Ano letivo** | 2025/2026 |
| **Autores** | Francisco Lopes, João Constantino |
| **Orientadores** | Professor Nuno Cota, Professor Gonçalo Esteves |

## Referências

- [Repositório oficial NetBox](https://github.com/netbox-community/netbox)
- [NetBox Topology Views](https://github.com/netbox-community/netbox-topology-views)
- [Documentação de desenvolvimento de plugins NetBox](https://netboxlabs.com/docs/netbox/plugins/development/)
- [vis-network Documentation](https://visjs.github.io/vis-network/docs/network/)
- [GNS3 Documentation](https://docs.gns3.com/)

---

<sub>Projeto Final de Curso — ISEL, 2026</sub>
