import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import uuid
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Hardcoded lists
aps_list = ['A', 'B', 'C', 'D']
linkset_list = ['1', '2', '3', '4', '5']

# Initial table data
table_data = []

# SVG paths or data for the icons
edit_icon_svg = '/assets/edit.png'
delete_icon_svg = './assets/delete.png'

# Modal for adding/editing filter
modal = dbc.Modal(
    [
        dbc.ModalHeader("Add/Edit Filter"),
        dbc.ModalBody([
            dbc.Label("APS:"),
            dcc.Dropdown(id='aps-dropdown', options=[{'label': aps, 'value': aps} for aps in aps_list]),
            html.Br(),
            dbc.Label("Linkset:"),
            dcc.Dropdown(id='linkset-dropdown', options=[{'label': ls, 'value': ls} for ls in linkset_list]),
            html.Br(),
            dbc.Label("Mode:"),
            dbc.RadioItems(
                id='mode-radio',
                options=[
                    {'label': 'Ingress', 'value': 'Ingress'},
                    {'label': 'Egress', 'value': 'Egress'}
                ],
                value='Ingress',
                inline=True
            ),
            html.Br(),
            dbc.Label("Test Mode (TM):"),
            dbc.Switch(id='tm-toggle',  value=False),
            html.Br(),
            dbc.Label("Trace Mode (TCM):"),
            dbc.Switch(id='tcm-toggle',  value=False),
        ]),
        dbc.ModalFooter([
            dbc.Button("Save", id="save-button", className="ml-auto"),
            dbc.Button("Cancel", id="cancel-button", className="ml-2")
        ]),
    ],
    id="modal",
    is_open=False,
    style={'border': '2px solid red'}  # Add red border
)

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Application Filtering"), width=10),
            dbc.Col(dbc.Button("Add Filter", id="add-filter-button", color="primary", className="float-right"), width=2),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("S.No"),
                            html.Th("APS"),
                            html.Th("Linkset"),
                            html.Th("Mode"),
                            html.Th("TM"),
                            html.Th("TCM"),
                            html.Th("Actions")
                        ])
                    ], style={'position': 'sticky', 'top': 0, 'background': 'white', 'zIndex': 1}),
                    html.Tbody(id="table-body")
                ], striped=True, bordered=True, hover=True, responsive=True),
                width=12
            )
        ]),
        modal,
        dcc.Store(id='edit-store'),
        dcc.Store(id='button-text-store', data='Save'),  # Store for button text
    ], fluid=True)
])

@app.callback(
    Output("modal", "is_open"),
    Output("save-button", "children"),  # Update button text
    Input("add-filter-button", "n_clicks"),
    Input("save-button", "n_clicks"),
    Input("cancel-button", "n_clicks"),
    Input({"type": "edit-button", "index": dash.ALL}, "n_clicks"),
    State("modal", "is_open"),
    State("button-text-store", "data"),
)
def toggle_modal(n1, n2, n3, edit_clicks, is_open, button_text):
    triggered_id = ctx.triggered_id

    if triggered_id == "add-filter-button":
        return not is_open, "Save"
    elif triggered_id == "save-button" or triggered_id == "cancel-button":
        return False, "Save"
    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'edit-button':
        return True, "Update"

    return is_open, button_text

@app.callback(
    Output("table-body", "children"),
    Output("aps-dropdown", "value"),
    Output("linkset-dropdown", "value"),
    Output("mode-radio", "value"),
    Output("tm-toggle", "value"),
    Output("tcm-toggle", "value"),
    Output("edit-store", "data"),
    Input("save-button", "n_clicks"),
    Input({"type": "edit-button", "index": dash.ALL}, "n_clicks"),
    Input({"type": "delete-button", "index": dash.ALL}, "n_clicks"),
    State("aps-dropdown", "value"),
    State("linkset-dropdown", "value"),
    State("mode-radio", "value"),
    State("tm-toggle", "value"),
    State("tcm-toggle", "value"),
    State("edit-store", "data"),
)
def update_table(save_clicks, edit_clicks, delete_clicks, aps, linkset, mode, tm, tcm, edit_data):
    global table_data
    
    triggered_id = ctx.triggered_id
    
    if triggered_id == "save-button":
        if all([aps, linkset]):
            if edit_data:
                # Update the existing entry
                index = edit_data['index']
                table_data[index] = {
                    'aps': aps,
                    'linkset': linkset,
                    'mode': mode,
                    'tm': tm,
                    'tcm': tcm
                }
            else:
                # Add a new entry
                table_data.append({
                    'aps': aps,
                    'linkset': linkset,
                    'mode': mode,
                    'tm': tm,
                    'tcm': tcm
                })
            return generate_table_rows(), None, None, 'Ingress', False, False, None
    
    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'edit-button':
        index = triggered_id['index']
        row = table_data[index]
        return generate_table_rows(), row['aps'], row['linkset'], row['mode'], row['tm'], row['tcm'], {'index': index}
    
    elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'delete-button':
        index = triggered_id['index']
        table_data.pop(index)
        return generate_table_rows(), None, None, 'Ingress', False, False, None
    
    return generate_table_rows(), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

def generate_table_rows():
    return [
        html.Tr([
            html.Td(i+1),
            html.Td(row['aps']),
            html.Td(row['linkset']),
            html.Td(row['mode']),
            html.Td(str(row['tm'])),
            html.Td(str(row['tcm'])),
            html.Td([
                dbc.Button(
                    [html.Img(src=edit_icon_svg, height="15px"), ""],
                    id={'type': 'edit-button', 'index': i},
                    color="primary",
                    size="sm",
                    className="mr-2"
                ),
                dbc.Button(
                    [html.Img(src=delete_icon_svg, height="15px"), ""],
                    id={'type': 'delete-button', 'index': i},
                    color="danger",
                    size="sm"
                ),
            ])
        ]) for i, row in enumerate(table_data)
    ]

if __name__ == '__main__':
    app.run_server(debug=True)
