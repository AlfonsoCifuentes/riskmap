
def fix_dash_integration(flask_app):
    """
    Corrección simplificada para integrar Dash con Flask
    """
    import dash
    from dash import html
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Crear aplicaciones Dash simples para prueba
        print("Creando dashboard histórico simplificado...")
        
        historical_app = dash.Dash(
            name="historical",
            server=flask_app,
            url_base_pathname="/dash/historical/",
            external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
        )
        
        historical_app.layout = html.Div([
            html.H1("Dashboard Histórico", style={'textAlign': 'center'}),
            html.Div([
                html.P("Dashboard histórico en desarrollo..."),
                html.P("Sistema integrado correctamente con Flask.")
            ], style={'margin': '20px'})
        ])
        
        print("Creando dashboard multivariable simplificado...")
        
        multivariate_app = dash.Dash(
            name="multivariate", 
            server=flask_app,
            url_base_pathname="/dash/multivariate/",
            external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
        )
        
        multivariate_app.layout = html.Div([
            html.H1("Análisis Multivariable", style={'textAlign': 'center'}),
            html.Div([
                html.P("Dashboard de análisis multivariable en desarrollo..."),
                html.P("Sistema integrado correctamente con Flask.")
            ], style={'margin': '20px'})
        ])
        
        print("✅ Dashboards integrados exitosamente")
        
        return {
            'historical': historical_app,
            'multivariate': multivariate_app
        }
        
    except Exception as e:
        logger.error(f"Error integrando dashboards: {e}")
        print(f"❌ Error: {e}")
        return None
