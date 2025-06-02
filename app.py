from flask import Flask, request, render_template_string
from scraper import scrape_ads

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    modell = ""
    if request.method == "POST":
        modell = request.form.get("modell")
        results = scrape_ads(modell)

    return render_template_string("""
        <html><head><title>Kleinanzeigen Scout</title></head><body>
        <h2>🔎 Kleinanzeigen Scout</h2>
        <form method="post">
            <input name="modell" placeholder="z.B. iPhone 14 Pro" value="{{ modell }}"/>
            <button type="submit">Suchen</button>
        </form>
        {% if results %}
            <h3>Ergebnisse:</h3>
            <ul>
            {% for item in results %}
                <li>
                    <img src="{{ item.image }}" width="100"/><br/>
                    <b>{{ item.title }}</b> – {{ item.price }} €<br/>
                    <a href="{{ item.link }}" target="_blank">🔗 Zur Anzeige</a>
                </li><br/>
            {% endfor %}
            </ul>
        {% endif %}
        </body></html>
    """, modell=modell, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)