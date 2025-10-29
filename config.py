
ASNR_RADIATION_URL = "https://mesure-radioactivite.fr/#/expert"
METEOFRANCE_WEATHER_DOWNLOAD_URL = "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f"
VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL = "https://www.data.gouv.fr/api/1/datasets/r/f5df602b-3800-44d7-b2df-fa40a0350325"
TIMEOUT = 10000 # Timeout en millisecondes pour les actions Playwright
INITIAL_TIMEOUT = 60000 # Timeout initial pour le lancement du navigateur et le chargement de la page
TIMEOUT_REFUSE_COOKIES = 100 # Timeout spécifique pour la bannière de cookies

SELECTORS = {
    "modal": {
        "container": "div.modal-content", 
        "button": "div.modal-content span.close"
    },
              
    "collection_environment": {
        "container": "div.row.container-select:has(div.label-select:has-text('Milieu de collecte'))",
        "button": ".selectric .button", 
        "options": ".selectricItems"
    },
    
    "dates": {
        "start": {
            "container": "div.row.container-select:has(div.label-select:has-text('Date de début'))", 
            "input": "input.form-control"
        },
        "end": {
            "container": "div.row.container-select:has(div.label-select:has-text('Date de fin'))", 
            "input": "input.form-control"
        },
    },
    
    "cookies": {
        "banner": "#tarteaucitronAlertBig", 
        "refuse": "#tarteaucitronAllDenied2"
    },
                
    "results": {
        "container": "div.row.container-select:has(button[ng-click='showResult()'])",
        "button": "button.btn.little-margin.middle-size.color-purple[ng-click='showResult()']"
    },

    "download": {
        "tab": {
            "container": "ul li:has-text('Téléchargement')",
            "button": "li[ng-click='showDownloadTree()']"
        },
        "download_button": "button[ng-click='downloadTree()']"
    }
}