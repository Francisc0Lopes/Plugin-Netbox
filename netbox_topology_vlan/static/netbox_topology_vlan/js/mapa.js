let globalDados = null; 
let networkMapa = null;

// A vacina: O código só corre quando a página estiver 100% carregada no browser
document.addEventListener('DOMContentLoaded', function() {
    
    const siteSelect = document.getElementById('site-select');
    const btnGerar = document.getElementById('btn-gerar');
    const vlanList = document.getElementById('vlan-checkbox-list');
    const helpText = document.getElementById('vlan-help-text');
    
    // Botões e painel de filtros
    const btnToggleFiltros = document.getElementById('btnToggleFiltros');
    const btnFecharFiltros = document.getElementById('btnFecharFiltros');
    const painelFiltros = document.getElementById('painelFiltros');

    // Ao clicar no botão "Filtros e Destaques" -> Alterna entre mostrar/esconder
    if (btnToggleFiltros && painelFiltros) {
        btnToggleFiltros.addEventListener('click', function(e) {
            e.preventDefault(); // Evita qualquer comportamento estranho de submissão
            painelFiltros.classList.toggle('d-none');
        });
    }

    // Ao clicar no "X" dentro do painel -> Oculta o painel adicionando 'd-none'
    if (btnFecharFiltros && painelFiltros) {
        btnFecharFiltros.addEventListener('click', function(e) {
            e.preventDefault();
            painelFiltros.classList.add('d-none');
        });
    }

    if (!siteSelect || !btnGerar) return; // Segurança extra

    // ==========================================
    // 1. PESQUISA DAS VLANS QUANDO O SITE MUDA
    // ==========================================
    siteSelect.addEventListener('change', function(e) {
        const siteId = e.target.value;
        
        // Se o utilizador voltar a escolher "-- Escolha o Site --"
        if (!siteId) {
            vlanList.innerHTML = '<div class="text-muted small mt-3 text-center">Selecione um site para pesquisar as VLANs.</div>';
            btnGerar.disabled = true;
            if(helpText) {
                helpText.textContent = "⚠ Selecione um Site primeiro";
                helpText.className = "text-danger fw-bold mt-1";
            }
            return;
        }

        // Animação visual enquanto espera pela resposta do servidor
        vlanList.innerHTML = '<div class="text-info small mt-3 text-center"><i class="mdi mdi-loading mdi-spin"></i> A pesquisar VLANs ativas neste site...</div>';
        btnGerar.disabled = true;

        // Vai à nova API buscar as VLANs ativas nas portas deste Site
        fetch(`/api/plugins/topology-vlan/get-site-vlans/?site_id=${siteId}`)
            .then(response => response.json())
            .then(data => {
                if (data.length === 0) {
                    vlanList.innerHTML = '<div class="text-danger small mt-3 text-center fw-bold">Nenhuma VLAN configurada neste site.</div>';
                    if(helpText) {
                        helpText.textContent = "Sem dados para desenhar.";
                        helpText.className = "text-danger fw-bold mt-1";
                    }
                    return;
                }
                
                // Constrói as caixas de seleção (Checkboxes) com base na resposta do servidor
                let html = '';
                data.forEach(v => {
                    html += `
                    <div class="form-check vlan-item mb-1">
                        <input class="form-check-input vlan-checkbox" type="checkbox" value="${v.id}" id="vlanCheck${v.id}">
                        <label class="form-check-label fw-bold" for="vlanCheck${v.id}" style="font-size: 13px; cursor: pointer;">
                            VLAN ${v.vid} - ${v.name}
                        </label>
                    </div>`;
                });
                
                vlanList.innerHTML = html;
                btnGerar.disabled = false;
                
                if(helpText) {
                    helpText.textContent = "✓ Pode marcar as redes que quer juntar";
                    helpText.className = "text-success fw-bold mt-1";
                }
            })
            .catch(err => {
                vlanList.innerHTML = '<div class="text-danger small mt-3 text-center">Erro ao comunicar com o servidor.</div>';
            });
    });

    // ==========================================
    // 2. BOTÃO GERAR O MAPA
    // ==========================================
    btnGerar.addEventListener('click', function() {
        // Apanha apenas as caixas que têm o 'certo' marcado
        const selecionadas = document.querySelectorAll('.vlan-checkbox:checked');
        if (selecionadas.length === 0) return alert('Selecione pelo menos uma VLAN na checklist.');

        // Junta os IDs por vírgulas (Ex: "10,20")
        const vlanIds = Array.from(selecionadas).map(cb => cb.value).join(',');
        const siteId = siteSelect.value;

        // Efeito visual de "A Carregar"
        document.getElementById('mapa-rede').style.opacity = '0.5';
        
        // Pede os dados da Topologia ao servidor
        fetch(`/api/plugins/topology-vlan/get-topology/?vlan_id=${vlanIds}&site_id=${siteId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('mapa-rede').style.opacity = '1';
                if (data.Erro) return alert(data.Erro);
                
                // Atualiza as caixas pretas de estatísticas
                document.getElementById('stat-nos').innerText = data.nos.length;
                document.getElementById('stat-ligacoes').innerText = data.ligacoes.length;
                const statVlan = document.getElementById('stat-vlan');
                const totalCheckboxes = Array.from(document.querySelectorAll('.vlan-checkbox')).filter(cb => {
                    const parent = cb.closest('.vlan-item');
                    return parent && parent.style.display !== 'none';
                }).length;                
                const totalSelecionadas = selecionadas.length;

                if (totalSelecionadas === 0) {
                    statVlan.innerText = "Nenhuma";
                } else if (totalSelecionadas === totalCheckboxes) {
                    statVlan.innerText = "Todas";
                } else if (totalSelecionadas > 3) {
                    statVlan.innerText = totalSelecionadas + " VLANs";
                } else {
                    statVlan.innerText = data.vlan; 
                }
                // Envia para o Vis.js desenhar
                desenharMapa(data);
            });
    });

    // ==========================================
    // 3. DESENHO DO MAPA E ÍCONES (Vis.js)
    // ==========================================

const svgRouter = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="#dc3545" stroke="#ffffff" stroke-width="2"/>
        <path d="M50 20v60m30-30H20" stroke="white" stroke-width="8" stroke-linecap="round"/>
        <path d="M40 30l10-10 10 10M40 70l10 10 10-10M30 40l-10 10 10 10M70 40l10 10-10 10" 
        fill="none" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;

const svgSwitch = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <rect width="90" height="60" x="5" y="20" rx="5" fill="#0d6efd" stroke="#ffffff" stroke-width="2"/>
        <path d="M15 45h70M50 45v35" stroke="#ffffff" stroke-width="5"/>
        <circle cx="20" cy="35" r="4" fill="#198754"/>
        <circle cx="35" cy="35" r="4" fill="#198754"/>
        <circle cx="50" cy="35" r="4" fill="#198754"/>
        <circle cx="65" cy="35" r="4" fill="#198754"/>
        <circle cx="80" cy="35" r="4" fill="#198754"/>
        <circle cx="20" cy="65" r="4" fill="white"/>
        <circle cx="35" cy="65" r="4" fill="white"/>
        <circle cx="50" cy="65" r="4" fill="white"/>
        <circle cx="65" cy="65" r="4" fill="white"/>
        <circle cx="80" cy="65" r="4" fill="white"/>
    </svg>`;

const svgServer = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <rect x="10" y="20" width="80" height="60" rx="5" fill="#28a745" stroke="#ffffff" stroke-width="2"/>
        <rect x="15" y="28" width="70" height="10" rx="2" fill="#198754"/>
        <rect x="15" y="45" width="70" height="10" rx="2" fill="#198754"/>
        <rect x="15" y="62" width="70" height="10" rx="2" fill="#198754"/>
        <circle cx="20" cy="33" r="2" fill="#00ff00"/>
        <circle cx="20" cy="50" r="2" fill="#00ff00"/>
        <circle cx="20" cy="67" r="2" fill="#00ff00"/>
        <rect x="75" y="30" width="8" height="6" fill="#ffffff"/>
        <rect x="75" y="47" width="8" height="6" fill="#ffffff"/>
        <rect x="75" y="64" width="8" height="6" fill="#ffffff"/>
    </svg>`;

const svgComputer =  `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <rect x="20" y="15" width="60" height="40" rx="5" fill="#0d6efd" stroke="#ffffff" stroke-width="2"/>
        <rect x="25" y="20" width="50" height="30" rx="2" fill="#ffffff"/>
        <rect x="40" y="55" width="20" height="5" fill="#0d6efd"/>
        <rect x="35" y="60" width="30" height="5" rx="2" fill="#adb5bd"/>
        <rect x="15" y="70" width="70" height="10" rx="2" fill="#6c757d"/>
        <circle cx="20" cy="75" r="1.5" fill="#ffffff"/>
        <circle cx="30" cy="75" r="1.5" fill="#ffffff"/>
        <circle cx="40" cy="75" r="1.5" fill="#ffffff"/>
        <circle cx="50" cy="75" r="1.5" fill="#ffffff"/>
        <circle cx="60" cy="75" r="1.5" fill="#ffffff"/>
        <circle cx="70" cy="75" r="1.5" fill="#ffffff"/>
    </svg>`;

    const svgUnknown = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
            <rect x="10" y="20" width="80" height="60" rx="5" fill="#6c757d" stroke="#ffffff" stroke-width="2"/>
            <text x="50" y="60" text-anchor="middle" fill="white" font-size="40" font-family="Arial" dy=".3em">?</text>
        </svg>`;

    function svgToDataUri(svg) {
        return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }

    const roleMatchers = [
        { match: r => r.includes('router'), icon: svgRouter },
        { match: r => r.includes('switch'), icon: svgSwitch },
        { match: r => r.includes('server'), icon: svgServer },
        { match: r => r.includes('pc') || r.includes('computer') || r.includes('notebook'), icon: svgComputer },
    ];

    function getDeviceIcon(role) {
        role = (role || "").toLowerCase();
        const found = roleMatchers.find(r => r.match(role));
        return found ? found.icon : svgUnknown;
}

    // Constrói o balão de informação quando se passa o rato na ligação
    function criarPopup(ligacao) {
        const template = document.getElementById('edge-popup-template');
        if(!template) return document.createElement('div');
        
        const clone = template.content.cloneNode(true);

        const modoA = ligacao.source_mode ? ligacao.source_mode.toLowerCase() : '';
        const modoB = ligacao.target_mode ? ligacao.target_mode.toLowerCase() : '';

        const div = document.createElement('div');
        div.appendChild(clone);

        // Mantém a tua estrutura original de preenchimento através da div:
        div.querySelector('.porta-a').textContent = ligacao.source_port;
        div.querySelector('.modo-a').textContent = ligacao.source_mode;
        div.querySelector('.porta-b').textContent = ligacao.target_port;
        div.querySelector('.modo-b').textContent = ligacao.target_mode;
        div.querySelector('.estado-stp').textContent = ligacao.stp_state || 'Forwarding';
        
        // A nossa validação de Erro Trunk vs Access (corrigida para a tua estrutura)
        const errorBox = div.querySelector('.error-mismatch-box');
        if (errorBox) {
            if ((modoA === 'trunk' && modoB === 'access') || (modoA === 'access' && modoB === 'trunk')) {
                errorBox.style.display = 'block'; // Mostra o aviso vermelho corrigido!
            } else {
                errorBox.style.display = 'none';  // Esconde se estiver tudo bem
            }
        }

        // Se a porta for Trunk, acende a informação das VLANs no popup
        if (ligacao.source_mode === 'Trunk' || ligacao.target_mode === 'Trunk') {
            div.querySelector('.trunk-vlans-box').style.display = 'block';
            div.querySelector('.trunk-vlans').textContent = ligacao.vlans_trunk || 'Todas'; 
        }
        // Se a porta for Access, acede a informação das VLANs no popup 
        else if (ligacao.source_mode === 'Access' || ligacao.target_mode === 'Access') {
            div.querySelector('.vlan-info-box').style.display = 'block';
            div.querySelector('.vlan-data').textContent = ligacao.vlan_access || 'Todas';
        }

        return div;
    }

function desenharMapa(dados) {
    globalDados = dados;

    const nodes = new vis.DataSet(
        dados.nos.map(no => ({
            id: no.id,
            label: no.name,
            url: no.url,
            shape: 'image',
            image: svgToDataUri(getDeviceIcon(no.role)),
            font: { 
                color: '#ffffff',  
                strokeWidth: 2,      
                strokeColor: '#000000', 
                size: 16,
                face: 'monospace',
            },
            shadow: { 
                enabled: true, 
                color: 'rgba(0,0,0,0.4)', 
                size: 8
            }
        }))
    );

    const edges = new vis.DataSet(dados.ligacoes.map(ligacao => {
    const isTrunk = ligacao.source_mode === 'Trunk' || ligacao.target_mode === 'Trunk';
    const corLigacao = isTrunk ? '#f97316' : '#64748b'; // Laranja para Trunk, Cinza para Access

            return {
                from: ligacao.source,
                to: ligacao.target,
                label: `${ligacao.source_port} ↔ ${ligacao.target_port}`,
                title: criarPopup(ligacao),
                dashes: isTrunk,
                color: { 
                    color: corLigacao,
                    highlight: '#00d4ff',
                    hover: '#00d4ff'
                },
                width: 3,
                font: { 
                    align: 'top',
                    size: 6,
                    color: '#000000',
                    strokeWidth: 2,   
                    strokeColor: '#ffffff',
                    face: 'monospace',
                },
                shadow: true
            };
        })
    );

    const container = document.getElementById('mapa-rede');
    if (!container) return;
    const data = { nodes, edges };

    const options = {
        physics: {
            enabled: true,
            forceAtlas2Based: {
                gravitationalConstant: -10000,
                springLength: 350,
                springConstant: 1
            },
            stabilization: { iterations: 200 }
        },
        interaction: {
            hover: true,
            navigationButtons: true,
            keyboard: true
        }
    };

    if (networkMapa !== null) {
        networkMapa.destroy();
        networkMapa = null;
    }

    networkMapa = new vis.Network(container, data, options);

    // Evento de duplo clique para navegação
    networkMapa.on("doubleClick", function (params) {
        if (params.nodes.length > 0) {
            const node = nodes.get(params.nodes[0]);
            if (node.url) {
                window.location.href = node.url;
            }
        }
    });
}

    // ==========================================
    // 4. BOTÕES DE EXPORTAÇÃO E IMPORTAÇÃO
    // ==========================================
    
    // EXPORTAR PNG
    const btnDownloadPNG = document.getElementById('btnDownloadPNG');
    if(btnDownloadPNG) {
        btnDownloadPNG.addEventListener('click', function() {
            const canvas = document.querySelector('#mapa-rede canvas');
            if (!canvas) return alert('Por favor, gere o mapa primeiro!');
            
            const tempCanvas = document.createElement('canvas');
            const tempCtx = tempCanvas.getContext('2d');
            tempCanvas.width = canvas.width; tempCanvas.height = canvas.height;
            tempCtx.fillStyle = '#1e1e24'; // Fundo Dark Theme
            tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
            tempCtx.drawImage(canvas, 0, 0);
            
            const link = document.createElement('a');
            link.download = 'Topologia_VLAN.png'; 
            link.href = tempCanvas.toDataURL('image/png'); 
            link.click();
        });
    }

    // EXPORTAR XML
    const btnDownloadXML = document.getElementById('btnDownloadXML');
    if(btnDownloadXML) {
        btnDownloadXML.addEventListener('click', function() {
            if (!globalDados) return alert('Por favor, gere o mapa primeiro!');
            let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<topologia>\n  <nos>\n';
            
            globalDados.nos.forEach(no => {
                xml += `    <no id="${no.id}" nome="${no.name.replace(/&/g, '&amp;').replace(/</g, '&lt;')}" role="${no.role}" />\n`;
            });
            xml += '  </nos>\n  <ligacoes>\n';
            globalDados.ligacoes.forEach(lig => {
                xml += `    <ligacao source="${lig.source}" target="${lig.target}" source_port="${lig.source_port}" target_port="${lig.target_port}" source_mode="${lig.source_mode}" target_mode="${lig.target_mode}" stp_state="${lig.stp_state}" />\n`;
            });
            xml += '  </ligacoes>\n</topologia>';
            
            const blob = new Blob([xml], { type: 'text/xml;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a'); 
            link.download = 'Topologia_VLAN.xml'; 
            link.href = url; 
            link.click(); 
            URL.revokeObjectURL(url);
        });
    }

    // ==========================================
    // EXPORTAR PARA GNS3 (.gns3)
    // ==========================================
    const btnDownloadGNS3 = document.getElementById('btnDownloadGNS3');
    if (btnDownloadGNS3) {
        btnDownloadGNS3.addEventListener('click', function() {
            if (!globalDados || globalDados.nos.length === 0) return alert('Por favor, gere o mapa primeiro antes de exportar.');

            const uuidv4 = () => {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            };

            // Esqueleto GNS3 rigoroso
            const gns3Project = {
                "name": "Topologia_Exportada_NetBox",
                "project_id": uuidv4(),
                "version": "2.2.0", 
                "type": "topology",
                "revision": 9,
                "topology": {
                    "computes": [],
                    "drawings": [],
                    "links": [],
                    "nodes": []
                }
            };

            const nodeUuids = {};
            const portCounters = {}; 

            globalDados.nos.forEach((no, index) => {
                const nUuid = uuidv4();
                nodeUuids[no.id] = nUuid; 
                portCounters[nUuid] = 0; 

                const posX = (index % 3) * 200 - 300;
                const posY = Math.floor(index / 3) * 200 - 300;
                
                // Prevenção contra nomes nulos na Base de Dados
                const safeName = no.name ? String(no.name) : ("Dispositivo_" + index);

                const role = (no.role || "").toLowerCase();
                let nodeType = "ethernet_switch"; 
                let symbol = ":/symbols/ethernet_switch.svg";
                let consoleType = "none";

                if (role.includes('router')) { 
                    symbol = ":/symbols/router.svg"; 
                    // Exportamos como switch genérico mas com símbolo de Router 
                    // para não rebentar com templates locais de QEMU do utilizador
                } 
                else if (role.includes('pc') || role.includes('host')) { 
                    nodeType = "vpcs"; 
                    symbol = ":/symbols/computer.svg"; 
                    consoleType = "telnet";
                }

                // Node construído com as regras estritas do Schema JSON do GNS3
                gns3Project.topology.nodes.push({
                    "compute_id": "local",
                    "console": consoleType === "none" ? null : (5000 + index), // Switches não podem ter consola
                    "console_auto_start": false,
                    "console_type": consoleType,
                    "custom_adapters": [],
                    "first_port_name": null,
                    "height": 59,
                    "label": {
                        "rotation": 0,
                        "style": "font-family: TypeWriter;font-size: 10.0;font-weight: bold;fill: #000000;fill-opacity: 1.0;",
                        "text": safeName,
                        "x": 10,
                        "y": -25
                    },
                    "locked": false,
                    "name": safeName,
                    "node_id": nUuid,
                    "node_type": nodeType,
                    "port_name_format": "Ethernet{0}",
                    "port_segment_size": 0,
                    "properties": {},
                    "symbol": symbol,
                    "width": 66,
                    "x": posX,
                    "y": posY,
                    "z": 1
                });
            });

            globalDados.ligacoes.forEach(lig => {
                const idSource = nodeUuids[lig.source];
                const idTarget = nodeUuids[lig.target];

                if (idSource && idTarget) {
                    const portSource = portCounters[idSource]++;
                    const portTarget = portCounters[idTarget]++;

                    gns3Project.topology.links.push({
                        "link_id": uuidv4(),
                        "nodes": [
                            { "adapter_number": 0, "node_id": idSource, "port_number": portSource },
                            { "adapter_number": 0, "node_id": idTarget, "port_number": portTarget }
                        ]
                    });
                }
            });

            const blob = new Blob([JSON.stringify(gns3Project, null, 4)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = 'Topologia_NetBox.gns3';
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
        });
    }


    // IMPORTAR GNS3
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const btnImportGNS3 = document.getElementById('btnImportGNS3');
    const fileGNS3 = document.getElementById('fileGNS3');
    
    if(btnImportGNS3 && fileGNS3) {
        btnImportGNS3.addEventListener('click', () => { fileGNS3.click(); });
        
        fileGNS3.addEventListener('change', function(e) {
            const file = e.target.files[0]; if (!file) return;
            const formData = new FormData(); formData.append('file', file);
            
            btnImportGNS3.innerHTML = '<i class="mdi mdi-loading mdi-spin"></i>';
            
            fetch('/api/plugins/topology-vlan/import-gns3/', { 
                method: 'POST', 
                headers: { 'X-CSRFToken': getCookie('csrftoken') }, 
                body: formData 
            })
            .then(response => response.json())
            .then(data => {
                btnImportGNS3.innerHTML = '<i class="mdi mdi-upload"></i> Importar GNS3';
                if (data.Erro) {
                    alert('Erro: ' + data.Erro); 
                } else { 
                    alert(`Sucesso! Foram criados ${data.criados} equipamentos.`); 
                    location.reload(); 
                }
            }).catch(err => {
                btnImportGNS3.innerHTML = '<i class="mdi mdi-upload"></i> Importar GNS3'; 
                alert('Erro na importação.');
            });
            e.target.value = ''; 
        });
    }

}); 

