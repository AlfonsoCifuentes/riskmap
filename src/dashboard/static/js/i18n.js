// Internationalization (i18n) Module

const translations = {
    es: {
        stats: {
            total_articles: "Total Artículos",
            high_risk: "Eventos Alto Riesgo",
            processed_today: "Procesados Hoy",
            active_regions: "Regiones Activas"
        },
        map: {
            title: "Mapa de Calor Global"
        },
        charts: {
            categories: "Distribución por Categorías",
            timeline: "Línea de Tiempo",
            sentiment: "Análisis de Sentimiento",
            wordcloud: "Nube de Palabras"
        },
        alerts: {
            title: "Alertas en Tiempo Real"
        },
        categories: {
            general_news: "Noticias Generales",
            military_conflict: "Conflicto Militar",
            economic_crisis: "Crisis Económica",
            political_tension: "Tensión Política",
            social_unrest: "Disturbios Sociales",
            natural_disaster: "Desastre Natural",
            cyber_security: "Ciberseguridad",
            health_crisis: "Crisis de Salud"
        },
        risk_levels: {
            low: "Bajo",
            medium: "Medio",
            high: "Alto",
            critical: "Crítico"
        }
    },
    en: {
        stats: {
            total_articles: "Total Articles",
            high_risk: "High Risk Events",
            processed_today: "Processed Today",
            active_regions: "Active Regions"
        },
        map: {
            title: "Global Heat Map"
        },
        charts: {
            categories: "Distribution by Categories",
            timeline: "Timeline",
            sentiment: "Sentiment Analysis",
            wordcloud: "Word Cloud"
        },
        alerts: {
            title: "Real-time Alerts"
        },
        categories: {
            general_news: "General News",
            military_conflict: "Military Conflict",
            economic_crisis: "Economic Crisis",
            political_tension: "Political Tension",
            social_unrest: "Social Unrest",
            natural_disaster: "Natural Disaster",
            cyber_security: "Cyber Security",
            health_crisis: "Health Crisis"
        },
        risk_levels: {
            low: "Low",
            medium: "Medium",
            high: "High",
            critical: "Critical"
        }
    },
    ru: {
        stats: {
            total_articles: "Всего статей",
            high_risk: "События высокого риска",
            processed_today: "Обработано сегодня",
            active_regions: "Активные регионы"
        },
        map: {
            title: "Глобальная тепловая карта"
        },
        charts: {
            categories: "Распределение по категориям",
            timeline: "Временная шкала",
            sentiment: "Анализ настроений",
            wordcloud: "Облако слов"
        },
        alerts: {
            title: "Оповещения в реальном времени"
        },
        categories: {
            general_news: "Общие новости",
            military_conflict: "Военный конфликт",
            economic_crisis: "Экономический кризис",
            political_tension: "Политическая напряженность",
            social_unrest: "Социальные волнения",
            natural_disaster: "Природная катастрофа",
            cyber_security: "Кибербезопасность",
            health_crisis: "Кризис здравоохра��ения"
        },
        risk_levels: {
            low: "Низкий",
            medium: "Средний",
            high: "Высокий",
            critical: "Критический"
        }
    },
    zh: {
        stats: {
            total_articles: "文章总数",
            high_risk: "高风险事件",
            processed_today: "今日处理",
            active_regions: "活跃地区"
        },
        map: {
            title: "全球热力图"
        },
        charts: {
            categories: "类别分布",
            timeline: "时间线",
            sentiment: "情感分析",
            wordcloud: "词云"
        },
        alerts: {
            title: "实时警报"
        },
        categories: {
            general_news: "一般新闻",
            military_conflict: "军事冲突",
            economic_crisis: "经济危机",
            political_tension: "政治紧张",
            social_unrest: "社会动荡",
            natural_disaster: "自然灾害",
            cyber_security: "网络安全",
            health_crisis: "健康危机"
        },
        risk_levels: {
            low: "低",
            medium: "中",
            high: "高",
            critical: "危急"
        }
    },
    ar: {
        stats: {
            total_articles: "إجمالي المقالات",
            high_risk: "أحداث عالية المخاطر",
            processed_today: "معالج اليوم",
            active_regions: "المناطق النشطة"
        },
        map: {
            title: "خريطة الحرارة العالمية"
        },
        charts: {
            categories: "التوزيع حسب الفئات",
            timeline: "الجدول الزمني",
            sentiment: "تحليل المشاعر",
            wordcloud: "سحابة الكلمات"
        },
        alerts: {
            title: "تنبيهات في الوقت الفعلي"
        },
        categories: {
            general_news: "أخبار عامة",
            military_conflict: "صراع عسكري",
            economic_crisis: "أزمة اقتصادية",
            political_tension: "توتر سياسي",
            social_unrest: "اضطرابات اجتماعية",
            natural_disaster: "كارثة طبيعية",
            cyber_security: "الأمن السيبراني",
            health_crisis: "أزمة صحية"
        },
        risk_levels: {
            low: "منخفض",
            medium: "متوسط",
            high: "عالي",
            critical: "حرج"
        }
    }
};

class I18n {
    constructor() {
        this.currentLanguage = 'es';
        this.translations = translations;
    }
    
    changeLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLanguage = lang;
            this.updatePageTranslations();
            
            // Update HTML lang attribute
            document.documentElement.lang = lang;
            
            // Update text direction for RTL languages
            if (lang === 'ar') {
                document.documentElement.dir = 'rtl';
                document.body.classList.add('rtl');
            } else {
                document.documentElement.dir = 'ltr';
                document.body.classList.remove('rtl');
            }
        }
    }
    
    updatePageTranslations() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.getTranslation(key);
            
            if (translation) {
                element.textContent = translation;
            }
        });
        
        // Update placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            const translation = this.getTranslation(key);
            
            if (translation) {
                element.placeholder = translation;
            }
        });
        
        // Update titles
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            const translation = this.getTranslation(key);
            
            if (translation) {
                element.title = translation;
            }
        });
    }
    
    getTranslation(key) {
        const keys = key.split('.');
        let translation = this.translations[this.currentLanguage];
        
        for (const k of keys) {
            if (translation && translation[k]) {
                translation = translation[k];
            } else {
                return key; // Return key if translation not found
            }
        }
        
        return translation;
    }
    
    translate(key, params = {}) {
        let translation = this.getTranslation(key);
        
        // Replace parameters in translation
        Object.keys(params).forEach(param => {
            translation = translation.replace(`{${param}}`, params[param]);
        });
        
        return translation;
    }
}

// Initialize i18n
window.i18n = new I18n();