from dash import Dash
from dash_upset import UpSet, from_counts

app = Dash(__name__)
app.layout = UpSet(
    id="upset",
    data=from_counts({
        "Python": 210,
        "R": 90,
        "SQL": 140,
        "Excel": 180,
        "Python&SQL": 160,
        "Python&Excel": 70,
        "SQL&Excel": 95,
        "Python&R": 65,
        "Python&SQL&Excel": 120,
        "Python&R&SQL": 55,
        "Python&R&SQL&Excel": 40,
    }),
    mode="intersect",
    theme="tol-light",
    inactive_color="#ffffff",
    title="Title",
    selection_color="#d55e00",
)

if __name__ == "__main__":
    app.run(debug=True)
