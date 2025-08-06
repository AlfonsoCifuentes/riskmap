"""
Dashboard de Prueba Simple para identificar errores JS
"""
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def test_dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Test Dashboard</title>
</head>
<body>
    <h1>Test Dashboard</h1>
    <div id="result">Cargando...</div>
    
    <script>
        console.log('Iniciando test...');
        
        // Test basic array syntax
        const testArray = [
            {
                title: "Test 1",
                location: "Test Location",
                risk: "high"
            },
            {
                title: "Test 2", 
                location: "Test Location 2",
                risk: "medium"
            }
        ];
        
        // Test function
        function openHeroArticleModal() {
            console.log('Function works!');
            return true;
        }
        
        // Test initialization
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded');
            document.getElementById('result').innerHTML = '✅ JavaScript trabajando correctamente!';
            openHeroArticleModal();
        });
        
        console.log('Script cargado exitosamente');
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    app.run(host='localhost', port=5002, debug=True)
