# Visualização Dinâmica e Automação de Topologias Lógicas (VLANs) em NetBox

## Introdução
Este projeto foca-se no desenvolvimento de um plugin para a plataforma NetBox, visando colmatar a lacuna existente na visualização de topologias lógicas de rede. Embora o NetBox ofereça visualização nativa da infraestrutura física, o mapeamento do percurso lógico de VLANs entre múltiplos equipamentos continua a ser um processo manual e complexo para administradores de rede.

O trabalho é desenvolvido no âmbito do Projeto Final de Curso da Licenciatura em Engenharia Informática, Redes e Telecomunicações (LEIRT) no ISEL.

## Objetivos
O objetivo principal é a criação de uma solução que permita:
**Automação de Mapas**: Gerar automaticamente diagramas de ligações lógicas.
**Isolamento de VLANs**: Permitir a visualização isolada do caminho de uma VLAN específica.
**Análise de Interfaces**: Identificar e distinguir automaticamente portas de acesso e portas de trunk.
**Interseção Técnica**: Aplicar conceitos de desenvolvimento de software (Python/Django) ao domínio da Engenharia de Redes.

## Tecnologias e Requisitos
O desenvolvimento do plugin assenta no seguinte stack tecnológico e áreas de conhecimento:
**Linguagem e Framework**: Python e Django.
**Integração**: Manipulação de APIs REST e modelos de dados do NetBox.
**Protocolos e Lógica de Redes**: Conceitos avançados de Switching e Routing, incluindo VLAN Propagation e lógica de Spanning Tree.
**Gestão de Dependências**: Utilização de `pyproject.toml` para conformidade com as normas atuais de empacotamento Python.

## Informações
* [cite_start]**Instituição**: Instituto Superior de Engenharia de Lisboa (ISEL).
* [cite_start]**Departamento**: Departamento de Engenharia de Electrónica e Telecomunicações e de Computadores (DEETC).
* [cite_start]**Curso**: Licenciatura em Engenharia Informática, Redes e Telecomunicações.
* [cite_start]**Ano Letivo**: 2025/2026.
* [cite_start]**Autor**: Francisco Lopes e João Constantino.

## Referências
* [cite_start][Repositório Oficial NetBox](https://github.com/netbox-community/netbox) 
* [cite_start][NetBox Topology Views](https://github.com/netbox-community/netbox-topology-views) 
* [cite_start][Documentação de Desenvolvimento de Plugins NetBox](https://netboxlabs.com/docs/netbox/plugins/development/) 