// Phish-Guard Landing Page - Live Stats & Interactions

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    // Refresh stats every 10 seconds
    setInterval(fetchStats, 10000);
});

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        // Hero stat
        const trustedEl = document.getElementById('trustedCount');
        if (trustedEl) {
            trustedEl.textContent = formatNumber(data.trusted_domains);
        }

        // Stats section
        const statTrusted = document.getElementById('statTrusted');
        const statCached = document.getElementById('statCached');
        const statBlocklist = document.getElementById('statBlocklist');
        const statModel = document.getElementById('statModel');

        if (statTrusted) statTrusted.textContent = formatNumber(data.trusted_domains);
        if (statCached) statCached.textContent = formatNumber(data.cached_predictions);
        if (statBlocklist) statBlocklist.textContent = formatNumber(data.blocklist_size);
        if (statModel) {
            statModel.textContent = data.model_status === 'active' ? 'Active' : 'Offline';
            statModel.style.color = data.model_status === 'active' ? '#00D395' : '#CF202F';
        }

    } catch (err) {
        console.log('Stats fetch failed (using mock data for demo):', err.message);
        // Fallback mock data for GitHub Pages demo
        const mockData = {
            trusted_domains: 1000000,
            cached_predictions: 1542,
            blocklist_size: 15,
            model_status: 'active'
        };
        document.getElementById('trustedCount').textContent = formatNumber(mockData.trusted_domains);
        document.getElementById('statTrusted').textContent = formatNumber(mockData.trusted_domains);
        document.getElementById('statCached').textContent = formatNumber(mockData.cached_predictions);
        document.getElementById('statBlocklist').textContent = formatNumber(mockData.blocklist_size);
        const statModel = document.getElementById('statModel');
        if (statModel) {
            statModel.textContent = 'Active (Demo)';
            statModel.style.color = '#00D395';
        }
    }
}

function formatNumber(num) {
    if (typeof num !== 'number') return '—';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
    return num.toString();
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});
