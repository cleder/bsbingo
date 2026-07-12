"""URL routes for the bingo app."""

from django.urls import URLPattern, URLResolver, path

from bingo import views

app_name = "bingo"

urlpatterns: list[URLPattern | URLResolver] = [
    path("", views.create_game, name="create_game"),
    path("game/<uuid:game_id>/join/", views.join_game, name="join_game"),
    path("board/<uuid:board_id>/", views.view_board, name="view_board"),
    path(
        "board/<uuid:board_id>/cell/<uuid:cell_id>/toggle/",
        views.toggle_cell,
        name="toggle_cell",
    ),
]
