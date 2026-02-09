/**
 * DEBUG SCRIPT - Frontend Dashboard Diagnostics
 * Injects debugging information directly into the page
 */

console.log('🔍 DEBUGGING SCRIPT LOADED');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 DOM is ready, starting diagnostics...');
    
    // Create debug panel
    const debugPanel = document.createElement('div');
    debugPanel.id = 'debug-panel';
    debugPanel.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: #00ff88;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 12px;
        z-index: 9999;
        max-width: 300px;
        border: 2px solid #00ff88;
    `;
    
    let debugInfo = '<strong>🔍 Dashboard Debug Info</strong><br>';
    
    // Check if we're on the right template
    const templateComment = document.documentElement.innerHTML.includes('DASHBOARD_BUENO_LOADED');
    debugInfo += `Template: ${templateComment ? '✓ DASHBOARD_BUENO' : '✗ Wrong template'}<br>`;
    
    // Check main sections
    const heroSection = document.getElementById('hero-article-section');
    const mosaicSection = document.getElementById('news-mosaic-section');
    const mainContainer = document.querySelector('.main-container');
    
    debugInfo += `Hero section: ${heroSection ? '✓ Present' : '✗ Missing'}<br>`;
    debugInfo += `Mosaic section: ${mosaicSection ? '✓ Present' : '✗ Missing'}<br>`;
    debugInfo += `Main container: ${mainContainer ? '✓ Present' : '✗ Missing'}<br>`;
    
    // Check functions
    const loadHeroExists = typeof window.loadHeroArticle === 'function';
    const loadMosaicExists = typeof window.loadMosaic === 'function';
    
    debugInfo += `loadHeroArticle(): ${loadHeroExists ? '✓ Exists' : '✗ Missing'}<br>`;
    debugInfo += `loadMosaic(): ${loadMosaicExists ? '✓ Exists' : '✗ Missing'}<br>`;
    
    // Check if Three.js loaded
    const threeExists = typeof THREE !== 'undefined';
    debugInfo += `Three.js: ${threeExists ? '✓ Loaded' : '✗ Missing'}<br>`;
    
    // Check API endpoints
    debugInfo += '<br><strong>🌐 API Tests</strong><br>';
    
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            debugInfo += `Status API: ✓ ${data.total_articles} articles<br>`;
            updateDebugPanel();
        })
        .catch(error => {
            debugInfo += `Status API: ✗ Failed<br>`;
            updateDebugPanel();
        });
    
    fetch('/api/hero-article')
        .then(response => response.json())
        .then(data => {
            debugInfo += `Hero API: ${data.success ? '✓ Working' : '✗ Failed'}<br>`;
            updateDebugPanel();
        })
        .catch(error => {
            debugInfo += `Hero API: ✗ Failed<br>`;
            updateDebugPanel();
        });
    
    fetch('/api/articles?limit=1')
        .then(response => response.json())
        .then(data => {
            debugInfo += `Articles API: ${data.success && data.articles ? '✓ Working' : '✗ Failed'}<br>`;
            updateDebugPanel();
        })
        .catch(error => {
            debugInfo += `Articles API: ✗ Failed<br>`;
            updateDebugPanel();
        });
    
    function updateDebugPanel() {
        debugPanel.innerHTML = debugInfo;
    }
    
    // Add visual indicators to sections
    if (heroSection) {
        heroSection.style.border = '3px solid #ff0000';
        heroSection.style.position = 'relative';
        const indicator = document.createElement('div');
        indicator.innerHTML = '🎯 HERO SECTION FOUND';
        indicator.style.cssText = 'position: absolute; top: 10px; left: 10px; background: #ff0000; color: white; padding: 5px; z-index: 9999; font-weight: bold;';
        heroSection.appendChild(indicator);
    }
    
    if (mosaicSection) {
        mosaicSection.style.border = '3px solid #0088ff';
        mosaicSection.style.position = 'relative';
        const indicator = document.createElement('div');
        indicator.innerHTML = '📰 MOSAIC SECTION FOUND';
        indicator.style.cssText = 'position: absolute; top: 10px; left: 10px; background: #0088ff; color: white; padding: 5px; z-index: 9999; font-weight: bold;';
        mosaicSection.appendChild(indicator);
    }
    
    // Add the debug panel to body
    document.body.appendChild(debugPanel);
    updateDebugPanel();
    
    // Force execute the functions if they exist
    setTimeout(() => {
        if (loadHeroExists) {
            console.log('🎯 Forcing hero load...');
            window.loadHeroArticle();
        }
        if (loadMosaicExists) {
            console.log('📰 Forcing mosaic load...');
            window.loadMosaic('real', null);
        }
    }, 2000);
});