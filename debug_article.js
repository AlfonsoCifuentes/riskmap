// Debug script for article of the day
console.log('🔍 Starting debug script...');

// Check if elements exist
const elementsToCheck = [
    'article-title',
    'article-summary', 
    'article-source',
    'article-date',
    'article-image',
    'article-language',
    'article-risk-badge'
];

console.log('📋 Checking if elements exist:');
elementsToCheck.forEach(id => {
    const element = document.getElementById(id);
    console.log(`${id}: ${element ? '✅ Found' : '❌ Not found'}`);
});

// Test the API call
async function debugArticleOfDay() {
    console.log('🚀 Starting API test...');
    
    try {
        console.log('📡 Fetching from /api/article-of-day');
        const response = await fetch('/api/article-of-day');
        console.log(`📊 Response status: ${response.status}`);
        console.log(`📊 Response ok: ${response.ok}`);
        
        const data = await response.json();
        console.log('📦 Full response data:', data);
        
        if (response.ok && data) {
            console.log('✅ Response is OK and has data');
            
            // Test updating each element
            const updates = [
                { id: 'article-title', value: data.title, label: 'Title' },
                { id: 'article-summary', value: data.content, label: 'Summary' },
                { id: 'article-source', value: data.source, label: 'Source' },
                { id: 'article-date', value: new Date(data.created_at).toLocaleDateString(), label: 'Date' },
                { id: 'article-image', value: data.image_url, label: 'Image' },
                { id: 'article-risk-badge', value: data.risk_level, label: 'Risk' }
            ];
            
            updates.forEach(update => {
                const element = document.getElementById(update.id);
                if (element) {
                    if (update.id === 'article-image') {
                        element.src = update.value || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80';
                        console.log(`🖼️ ${update.label}: Set image src to ${element.src}`);
                    } else if (update.id === 'article-risk-badge') {
                        element.className = `risk-badge risk-${update.value.toLowerCase()}`;
                        element.textContent = update.value + ' RISK';
                        console.log(`⚠️ ${update.label}: Set to ${element.textContent} with class ${element.className}`);
                    } else {
                        element.textContent = update.value;
                        console.log(`📝 ${update.label}: Set to "${update.value}"`);
                    }
                } else {
                    console.log(`❌ ${update.label}: Element not found!`);
                }
            });
            
            console.log('🎉 All updates completed!');
        } else {
            console.log('❌ Response not OK or no data');
        }
        
    } catch (error) {
        console.error('💥 Error:', error);
    }
}

// Wait for page to load, then run debug
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', debugArticleOfDay);
} else {
    debugArticleOfDay();
}
