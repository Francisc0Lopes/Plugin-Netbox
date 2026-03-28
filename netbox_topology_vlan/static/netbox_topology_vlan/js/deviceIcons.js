    // --- Definição de Ícones SVG (Para garantir fidelidade profissional) ---
    // Router (Círculo vermelho com setas)
    const svgRouter = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="#dc3545" stroke="#ffffff" stroke-width="2"/>
        <path d="M50 20v60m30-30H20" stroke="white" stroke-width="8" stroke-linecap="round"/>
        <path d="M40 30l10-10 10 10M40 70l10 10 10-10M30 40l-10 10 10 10M70 40l10 10-10 10" 
            fill="none" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    `;
    // Switch (Retângulo azul com portas)
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
    </svg>
    `;
    // Server (Retângulo verde com detalhes)
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
    </svg>
    `;

    const svgUnknown = `
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <rect x="10" y="20" width="80" height="60" rx="5" fill="#6c757d" stroke="#ffffff" stroke-width="2"/>
        
        <text x="50" y="60" text-anchor="middle" fill="white" font-size="40" font-family="Arial" dy=".3em">
            ?
        </text>
    </svg>`;


const roleMatchers = [
    { match: r => r.includes('router'), icon: svgRouter },
    { match: r => r.includes('switch'), icon: svgSwitch },
    { match: r => r.includes('server'), icon: svgServer }, //Acrescentar mais ícones 
];

function getDeviceIcon(role) {
    role = (role || "").toLowerCase();
    const found = roleMatchers.find(r => r.match(role));
    return found ? found.icon : svgUnknown;
}

function svgToDataUri(svg) {
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}