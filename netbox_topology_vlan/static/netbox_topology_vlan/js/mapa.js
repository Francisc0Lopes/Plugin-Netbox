let globalDados = null; 

// ==========================================
// TRUQUE UX: Seleção Múltipla sem a tecla CTRL
// ==========================================
document.getElementById('vlan-select').addEventListener('mousedown', function(e) {
    if (e.target.tagName === 'OPTION') {
        e.preventDefault(); // Impede o comportamento padrão do browser
        e.target.selected = !e.target.selected; // Inverte o estado (Selecionado <-> Não Selecionado)
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

// ==========================================
// ÍCONES E DESENHO DO MAPA
// ==========================================
const svgRouter = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#0d6efd" stroke="#ffffff" stroke-width="3"/><path d="M50 20v60m30-30H20" stroke="white" stroke-width="8" stroke-linecap="round"/><path d="M40 30l10-10 10 10M40 70l10 10 10-10M30 40l-10 10 10 10M70 40l10 10-10 10" fill="none" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const svgSwitch = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="90" height="60" x="5" y="20" rx="8" fill="#0d6efd" stroke="#ffffff" stroke-width="3"/><path d="M15 45h70M50 45v35" stroke="#ffffff" stroke-width="5"/><circle cx="20" cy="35" r="4" fill="#ffffff"/><circle cx="35" cy="35" r="4" fill="#ffffff"/><circle cx="50" cy="35" r="4" fill="#ffffff"/><circle cx="65" cy="35" r="4" fill="#ffffff"/><circle cx="20" cy="65" r="4" fill="#ffffff"/><circle cx="50" cy="65" r="4" fill="#ffffff"/><circle cx="80" cy="65" r="4" fill="#ffffff"/></svg>`;

function svgToDataUri(svg) { return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg); }

function getDeviceIcon(role) {
    role = (role || "").toLowerCase();
    if (role.includes('router')) return svgRouter;
    if (role.includes('switch')) return svgSwitch;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect x="10" y="20" width="80" height="60" rx="5" fill="#6c757d" stroke="#ffffff" stroke-width="2"/><text x="50" y="60" text-anchor="middle" fill="white" font-size="40">?</text></svg>`;
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
// BOTÃO GERAR (ATUALIZADO)
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
            
            document.getElementById('stat-nos').innerText = data.nos.length;
            document.getElementById('stat-ligacoes').innerText = data.ligacoes.length;
            document.getElementById('stat-vlan').innerText = data.vlan;

            desenharMapa(data);
        });
});

function desenharMapa(dados) {
    globalDados = dados; 

    const nodes = new vis.DataSet(dados.nos.map(no => ({
        id: no.id, label: no.name, shape: 'image', image: svgToDataUri(getDeviceIcon(no.role)),
        font: { color: '#334155', size: 14, face: 'monospace', vadjust: 55, bold: true },
        shadow: { enabled: true, color: 'rgba(0,0,0,0.1)', size: 5 }
    })));

    const edges = new vis.DataSet(dados.ligacoes.map(ligacao => {
        const isTrunk = ligacao.source_mode === 'Trunk' || ligacao.target_mode === 'Trunk';
        const corLigacao = isTrunk ? '#f97316' : '#475569';

        return {
            from: ligacao.source, to: ligacao.target,
            label: ligacao.source_port + ' ↔ ' + ligacao.target_port,
            title: criarPopup(ligacao),
            dashes: isTrunk, 
            color: { color: corLigacao, highlight: '#3b82f6', hover: '#0ea5e9' },
            width: 3, 
            font: { align: 'top', size: 11, color: '#475569', background: 'rgba(241, 245, 249, 0.85)' },
            smooth: { type: 'continuous' }
        };
    }));

    new vis.Network(document.getElementById('mapa-rede'), { nodes, edges }, {
        physics: { forceAtlas2Based: { gravitationalConstant: -120, springLength: 220 } },
        interaction: { hover: true, tooltipDelay: 100 }
    });
}

// ==========================================
// DOWNLOADS E IMPORTAÇÃO
// ==========================================
document.getElementById('btnDownloadPNG').addEventListener('click', function() {
    const canvas = document.querySelector('#mapa-rede canvas');
    if (!canvas) return alert('Por favor, gere o mapa primeiro!');

    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    
    tempCtx.fillStyle = '#f1f5f9';
    tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
    tempCtx.drawImage(canvas, 0, 0);

    const link = document.createElement('a');
    link.download = 'Topologia_VLAN.png';
    link.href = tempCanvas.toDataURL('image/png');
    link.click();
});

document.getElementById('btnDownloadXML').addEventListener('click', function() {
    if (!globalDados) return alert('Por favor, gere o mapa primeiro!');

    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<topologia>\n';
    xml += '  <nos>\n';
    globalDados.nos.forEach(no => {
        const safeName = no.name.replace(/&/g, '&amp;').replace(/</g, '&lt;');
        xml += `    <no id="${no.id}" nome="${safeName}" role="${no.role}" />\n`;
    });
    xml += '  </nos>\n';
    xml += '  <ligacoes>\n';
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

window.onload = () => { 
    if (document.getElementById('vlan-select') && document.getElementById('vlan-select').selectedOptions.length > 0) {
        document.getElementById('btn-gerar').click(); 
    }
};

