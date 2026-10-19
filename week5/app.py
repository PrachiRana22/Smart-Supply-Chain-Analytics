"""Interactive dashboard: Smart Supply Chain Analytics.   Run:  python app.py   then open http://127.0.0.1:8050
Needs: pip install dash plotly pandas"""

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import dash_data as dd

PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#7F7F7F"]
df = dd.load_data("DataCoSupplyChainDataset.csv")  # change the path if needed

app = Dash(__name__)
app.title = "Smart Supply Chain Analytics"


def tile(title, comp_id):
    return html.Div(
        [
            html.Div(title, style={"fontSize": 12, "color": "#555"}),
            html.Div(id=comp_id, style={"fontSize": 26, "fontWeight": 700, "color": "#1F3864"}),
        ],
        style={"flex": 1, "padding": 12, "background": "#F2F6FA", "borderRadius": 8},
    )


app.layout = html.Div(
    style={"fontFamily": "Calibri, Arial", "maxWidth": 1200, "margin": "auto", "padding": 16},
    children=[
        html.H2("Smart Supply Chain Analytics"),
        html.Div(
            [
                dcc.Dropdown(
                    sorted(df["Market"].unique()),
                    multi=True,
                    placeholder="Market (all)",
                    id="f-market",
                    style={"flex": 1},
                ),
                dcc.Dropdown(
                    sorted(df["Shipping Mode"].unique()),
                    multi=True,
                    placeholder="Shipping mode (all)",
                    id="f-mode",
                    style={"flex": 1},
                ),
                dcc.DatePickerRange(
                    id="f-dates",
                    min_date_allowed=df["order_date"].min().date(),
                    max_date_allowed=df["order_date"].max().date(),
                    start_date=df["order_date"].min().date(),
                    end_date=df["order_date"].max().date(),
                ),
            ],
            style={"display": "flex", "gap": 12, "marginBottom": 12},
        ),
        html.Div(
            [
                tile("Sales", "k-sales"),
                tile("Profit margin", "k-margin"),
                tile("Orders", "k-orders"),
                tile("Late deliveries (cancelled excluded)", "k-late"),
            ],
            style={"display": "flex", "gap": 12},
        ),
        html.Div(
            [dcc.Graph(id="g-trend", style={"flex": 2}), dcc.Graph(id="g-late", style={"flex": 1})],
            style={"display": "flex"},
        ),
        html.Div(
            [
                dcc.Graph(id="g-margin", style={"flex": 1}),
                dcc.Graph(id="g-discount", style={"flex": 1}),
            ],
            style={"display": "flex"},
        ),
        html.P(
            "Note: from October 2017 orders are recorded with about one item per order, so monthly totals before and after "
            "that date are not directly comparable.",
            style={"fontSize": 12, "color": "#555"},
        ),
    ],
)


@app.callback(
    Output("k-sales", "children"),
    Output("k-margin", "children"),
    Output("k-orders", "children"),
    Output("k-late", "children"),
    Output("g-trend", "figure"),
    Output("g-late", "figure"),
    Output("g-margin", "figure"),
    Output("g-discount", "figure"),
    Input("f-market", "value"),
    Input("f-mode", "value"),
    Input("f-dates", "start_date"),
    Input("f-dates", "end_date"),
)
def update(markets, modes, start, end):
    d = dd.filter_data(df, markets, modes, start, end)
    k = dd.kpis(d)
    trend = px.line(
        dd.monthly(d), x="month", y="sales", title="Monthly sales", color_discrete_sequence=PALETTE
    )
    trend.add_vline(x="2017-10-01", line_dash="dash", annotation_text="recording change")
    late = px.bar(
        dd.late_by_mode(d),
        x="late_rate",
        y="Shipping Mode",
        orientation="h",
        title="Late rate by shipping mode",
        color_discrete_sequence=[PALETTE[3]],
    )
    late.update_xaxes(tickformat=".0%", range=[0, 1])
    margin = px.bar(
        dd.margin_by_category(d),
        x="margin",
        y="Category Name",
        orientation="h",
        title="Profit margin, top 15 categories by sales",
        color_discrete_sequence=[PALETTE[0]],
    )
    margin.update_xaxes(tickformat=".0%")
    margin.update_yaxes(autorange="reversed")
    disc = px.bar(
        dd.profit_by_discount(d),
        x="discount_band",
        y="Order Profit Per Order",
        title="Average profit per item by discount rate",
        color_discrete_sequence=[PALETTE[2]],
    )
    return (
        f"{k['sales']/1e6:,.2f} M",
        f"{k['margin']:.1%}",
        f"{k['orders']:,}",
        f"{k['late_rate']:.1%}",
        trend,
        late,
        margin,
        disc,
    )


if __name__ == "__main__":
    app.run(debug=False)
