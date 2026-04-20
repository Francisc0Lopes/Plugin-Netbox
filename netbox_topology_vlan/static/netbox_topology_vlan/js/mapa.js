let globalDados = null;

// =========================
// MULTI SELECT SEM CTRL
// =========================
document.getElementById('vlan-select').addEventListener('mousedown', function(e) {
    if (e.target.tagName === 'OPTION') {
        e.preventDefault();
        e.target.selected = !e.target.selected;
    }
});

// ==========================================
// LÓGICA DE DESBLOQUEIO E FILTRO DE SITES
// ==========================================

document.getElementById('site-select').addEventListener('change', function(e) {
    const siteId = e.target.value;
    const vlanSelect = document.getElementById('vlan-select');
    const btnGerar = document.getElementById('btn-gerar');
    const helpText = document.getElementById('vlan-help-text');
    
    // Se o utilizador voltar a "Escolher o Site" (vazio), tranca tudo de novo
    if (!siteId) {
        vlanSelect.disabled = true;
        btnGerar.disabled = true;
        if(helpText) {
            helpText.textContent = "⚠ Selecione um Site primeiro";
            helpText.className = "text-danger fw-bold";
        }
        return;
    }

    // Se escolheu um site válido, destranca!
    vlanSelect.disabled = false;
    btnGerar.disabled = false;
    if(helpText) {
        helpText.textContent = "(Clique para selecionar. Não precisa de CTRL)";
        helpText.className = "text-success fw-bold";
    }

    // Mostra só as VLANs deste Site (ou VLANs globais que não tenham site atribuído)
    const options = vlanSelect.options;
    for (let i = 0; i < options.length; i++) {
        const opt = options[i];
        const optSite = opt.getAttribute('data-site');
        
        if (!optSite || optSite === siteId) {
            opt.style.display = ''; // Mostra
        } else {
            opt.style.display = 'none'; // Esconde as que são de outros sites
            opt.selected = false;       // Garante que são desmarcadas
        }
    }
});

// =========================
// SVG ICONS
// =========================

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

function criarPopup(ligacao) {
    const template = document.getElementById('edge-popup-template');
    const clone = template.content.cloneNode(true);
    const div = document.createElement('div');
    div.appendChild(clone);

    div.querySelector('.porta-a').textContent = ligacao.source_port;
    div.querySelector('.modo-a').textContent = ligacao.source_mode;
    div.querySelector('.porta-b').textContent = ligacao.target_port;
    div.querySelector('.modo-b').textContent = ligacao.target_mode;
    div.querySelector('.estado-stp').textContent = ligacao.stp_state || 'Forwarding';
        
    const isTrunk = ligacao.source_mode === 'Trunk' || ligacao.target_mode === 'Trunk';
    if (isTrunk) {
        div.querySelector('.trunk-vlans-box').style.display = 'block';
        div.querySelector('.trunk-vlans').textContent = ligacao.vlans_trunk || 'Todas'; 
    }
    return div;
}


// ==========================================
// BOTÃO GERAR 
// ==========================================

document.getElementById('btn-gerar').addEventListener('click', function() {
    const selecionadas = Array.from(document.getElementById('vlan-select').selectedOptions);
    if (selecionadas.length === 0) return alert('Por favor, selecione pelo menos uma VLAN.');

    const vlanIds = selecionadas.map(opt => opt.value).join(',');
    // Vai buscar o Site escolhido (se existir)
    const siteElement = document.getElementById('site-select');
    const siteId = siteElement ? siteElement.value : '';

    document.getElementById('mapa-rede').style.opacity = '0.5';
    
    // Envia agora os DOIS parâmetros para a API: vlan_id e site_id
    fetch(`/api/plugins/topology-vlan/get-topology/?vlan_id=${vlanIds}&site_id=${siteId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('mapa-rede').style.opacity = '1';
            if (data.Erro) return alert(data.Erro);
            globalDados = data;
            document.getElementById('stat-nos').innerText = data.nos.length;
            document.getElementById('stat-ligacoes').innerText = data.ligacoes.length;
            document.getElementById('stat-vlan').innerText = data.vlan;

            desenharMapa(data);
        });
});

// =========================
// DESENHAR MAPA
// =========================

function desenharMapa(dados) {

    var nodes = new vis.DataSet(
        dados.nos.map(no => {
            return {
                id: no.id,
                label: no.name,
                url : no.url,
                shape: 'image',
                image: svgToDataUri(getDeviceIcon(no.role)), 
                font: { 
                    color: '#ffffff',
                    size: 14,
                    face: 'monospace',
                },
                shadow: { enabled: true, color: 'rgba(0,0,0,0.5)', size: 8 }
            };
        })
    );

    var edges = new vis.DataSet(
        dados.ligacoes.map(ligacao => {
            // Lógica de determinação de cor e estilo para Access/Trunk
            let borderColor = '#198754'; // Default: Verde (Unknown)
            let isDashed = false;

            console.log(`Ligação ${ligacao.source} ↔ ${ligacao.target}: source_mode=${ligacao.source_mode}, target_mode=${ligacao.target_mode}`);
            if (ligacao.source_mode === 'Trunk' || ligacao.target_mode === 'Trunk') {
                borderColor = '#fd7e14'; // Laranja Trunk
                isDashed = true;
            } else if (ligacao.source_mode === 'Access' || ligacao.target_mode === 'Access') {
                borderColor = '#0000f9'; // Azul Access
                isDashed = true;
            }
            return {
                from: ligacao.source,
                to: ligacao.target,
                label: ligacao.source_port + ' ↔ ' + ligacao.target_port,
                title: criarPopup(ligacao),
                dashes: isDashed, 
                color: { 
                    color: borderColor,
                    highlight: '#00d4ff',
                    hover: '#ffffff'
                },
                width: 3,
                font: { 
                    align: 'top', 
                    size: 9, 
                    color: '#adb5bd' 
                },
                shadow: true
            };
        })
    );

    var container = document.getElementById('mapa-rede');
    var data = { nodes: nodes, edges: edges };
        
    var options = {
        physics: { 
            enabled: true,
            barnesHut: { 
                gravitationalConstant: -7000, 
                springLength: 200,
                springConstant: 0.04
            },
            stabilization: { iterations: 150 }
        },
        interaction: {
            hover: true,
            navigationButtons: true, // Adiciona botões de zoom profissionais
            keyboard: true
        }
    };

    var network = new vis.Network(container, data, options);

    network.on("doubleClick", function (params) {
    if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.get(nodeId);
        console.log("Tentando navegar para:", node.url); // Debug

        if (node.url) {
            window.location.href = node.url;
            }
        }
    });
}

// =========================
// DOWNLOAD PNG
// =========================

document.getElementById('btnDownloadPNG').addEventListener('click', function() {

    const canvas = document.querySelector('#mapa-rede canvas');
    if (!canvas) return alert('Gera primeiro o mapa');

    const link = document.createElement('a');
    link.download = 'topologia.png';
    link.href = canvas.toDataURL();
    link.click();
});

// =========================
// DOWNLOAD XML
// =========================

document.getElementById('btnDownloadXML').addEventListener('click', function() {

    if (!globalDados) return alert('Gera primeiro o mapa');

    let xml = '<topologia>';

    globalDados.nos.forEach(n => {
        xml += `<no id="${n.id}" nome="${n.name}" />`;
    });

    globalDados.ligacoes.forEach(l => {
        xml += `<ligacao source="${l.source}" target="${l.target}" />`;
    });

    xml += '</topologia>';

    const blob = new Blob([xml], { type: 'text/xml' });

    const link = document.createElement('a');
    link.download = 'topologia.xml';
    link.href = URL.createObjectURL(blob);
    link.click();
});

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

document.getElementById('btnImportGNS3').addEventListener('click', () => {
    document.getElementById('fileGNS3').click();
});

document.getElementById('fileGNS3').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    document.getElementById('btnImportGNS3').innerHTML = '<i class="mdi mdi-loading mdi-spin"></i> A Importar...';

    fetch('/api/plugins/topology-vlan/import-gns3/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('btnImportGNS3').innerHTML = '<i class="mdi mdi-upload"></i> Importar GNS3';
        if (data.Erro) alert('Erro na importação: ' + data.Erro);
        else { alert(`Sucesso! Foram criados ${data.criados} equipamentos.`); location.reload(); }
    })
    .catch(err => {
        document.getElementById('btnImportGNS3').innerHTML = '<i class="mdi mdi-upload"></i> Importar GNS3';
        console.error(err); alert('Erro na importacão');
    });
    e.target.value = ''; 
});

// =========================
// AUTO LOAD
// =========================

window.onload = function() {
    const vlanSelect = document.getElementById('vlan-select');
    if (vlanSelect.value !== "") {
        // "Clica" no botão por nós
        document.getElementById('btn-gerar').click();
    }
};
