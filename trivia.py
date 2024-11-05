import flet as ft
import time
import threading
import random
from db import questions

class TriviaGame(ft.UserControl):
    MAX_TIMER = 15  # Constante para el tiempo máximo

    def __init__(self):
        super().__init__()
        self.current_question = 0
        self.score = 0
        self.timer = self.MAX_TIMER
        self.timer_thread = None
        self.timer_running = False
        self.game_started = False
        self.username = ""
        self.incorrect_answers = []

        # Etiqueta para mostrar mensajes de error
        self.error_message = ft.Text(value="", color="red", size=16, visible=False)

    def build(self):
        self.username_input = ft.TextField(label="Ingresa tu usuario", width=300, visible=True)

        # Dropdown para seleccionar la categoría
        self.category_dropdown = ft.Dropdown(
            label="Selecciona una categoría",
            options=[ft.dropdown.Option(cat) for cat in questions.keys()],
            visible=True,
            width=300
        )

        self.question_text = ft.Text(value="FleTrivia", size=28, text_align="center", color="white", visible=True)

        # Definir el texto del temporizador
        self.timer_text = ft.Text(value=f"⏰ {self.timer} s", size=18, color="red", visible=False)

        self.start_button = ft.IconButton(
            on_click=self.start_game,
            icon_color="white",
            icon=ft.icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                bgcolor="green"
            )
        )
        
        self.restart_button = ft.IconButton(
            on_click=self.restart_game,
            icon_color="white",
            visible=False,
            icon=ft.icons.RESTART_ALT,
            style=ft.ButtonStyle(
                bgcolor="orange"
            )
        )

        self.exit_button = ft.IconButton(
            on_click=self.exit_game,
            icon_color="white",
            visible=False,
            icon=ft.icons.CANCEL,
            style=ft.ButtonStyle(
                bgcolor="red"
            )
        )

        # Definir los botones de opción
        self.option_buttons = [
            ft.ElevatedButton(
                text=f"Opción {i+1}",
                on_click=self.check_answer,
                color="cyan",
                visible=False  # Inicialmente ocultos
            ) for i in range(4)
        ]

        # Contenedor para mostrar las respuestas incorrectas
        self.summary_view = ft.ListView(
            controls=[],
            visible=False,
            height=400,
            width=500,
            spacing=10,
            padding=10,
        )

        # Layout
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.exit_button],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10
                    ),
                    self.question_text,
                    self.username_input,
                    self.category_dropdown,
                    self.timer_text,
                    self.error_message,  # Agregar la etiqueta de error aquí
                    ft.Container(
                        content=self.start_button,
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=20)
                    ),
                    self.restart_button,
                    *self.option_buttons,
                    self.summary_view,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ),
            width=550,
            height=750,
            bgcolor="#333333",
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(10),
            expand=True
        )
        
    def show_error(self, message):
        self.error_message.value = message
        self.error_message.visible = True
        self.update()

    def hide_error(self):
        self.error_message.value = ""
        self.error_message.visible = False
        self.update()

    def start_game(self, e=None):
        self.username = self.username_input.value.strip()
        selected_category = self.category_dropdown.value
        
        # Verificación de datos
        if not self.username:
            self.show_error("Por favor ingresa tu usuario.")
            return
        
        elif len(self.username) < 3:
            self.show_error("El nombre debe tener al menos 3 caracteres.")
            return
        
        if not selected_category:
            self.show_error("Por favor selecciona una categoría.")
            return

        # Si todo está bien, oculta el mensaje de error y continúa con el inicio del juego
        self.hide_error()
        self.start_button.visible = False
        self.restart_button.visible = False
        self.username_input.visible = False
        self.category_dropdown.visible = False
        self.current_question = 0
        self.score = 0
        self.timer = self.MAX_TIMER
        self.incorrect_answers = []
        self.timer_text.value = f"⏰ {self.timer} s"
        self.timer_text.visible = True
        self.game_started = True
        self.summary_view.visible = False

        self.question_text.visible = True
        self.exit_button.visible = True
        for btn in self.option_buttons:
            btn.visible = True

        self.questions = questions[selected_category]
        self.load_question()
        self.start_timer()

    def load_question(self):
        if not self.questions:
            self.question_text.value = "No hay preguntas disponibles."
            self.update()
            return

        question_data = self.questions[self.current_question]
        self.question_text.value = question_data["question"]

        options = question_data["options"]
        random.shuffle(options)
        for i, option in enumerate(options):
            self.option_buttons[i].text = option
            self.option_buttons[i].visible = True
        self.update()

    def check_answer(self, e):
        selected_option = e.control.text
        correct_answer = self.questions[self.current_question]["answer"]
        if selected_option == correct_answer:
            self.score += 1
        else:
            self.incorrect_answers.append({
                "question": self.questions[self.current_question]["question"],
                "correct_answer": correct_answer,
                "selected_answer": selected_option
            })
        self.stop_timer()
        self.next_question()

    def next_question(self):
        self.current_question += 1
        if self.current_question < len(self.questions):
            self.load_question()
            self.timer = self.MAX_TIMER
            self.start_timer()
        else:
            self.end_game()

    def end_game(self):
        self.stop_timer()
        self.question_text.value = f"Fin del juego! {self.username} ha obtenido: {self.score}/{len(self.questions)}"
        for btn in self.option_buttons:
            btn.visible = False
        self.timer_text.visible = False
        self.restart_button.visible = True
        self.exit_button.visible = False
        self.show_summary()
        self.update()

    def show_summary(self):
        self.summary_view.controls.clear()
        if self.incorrect_answers:
            for item in self.incorrect_answers:
                summary_item = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Pregunta: {item['question']}", color="white", size=16),
                            ft.Text(f"Tu respuesta: {item['selected_answer']}", color="orange", size=14),
                            ft.Text(f"Respuesta correcta: {item['correct_answer']}", color="green", size=14)
                        ],
                        spacing=5
                    ),
                    padding=ft.padding.all(10),
                    bgcolor="#444444",
                    border_radius=ft.border_radius.all(8),
                )
                self.summary_view.controls.append(summary_item)
            self.summary_view.visible = True
        else:
            self.summary_view.controls.append(
                ft.Container(
                    content=ft.Text("¡Felicidades! No tuviste respuestas incorrectas."),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(10)
                )
            )
            self.summary_view.visible = True

    def start_timer(self):
        if self.timer_running:
            self.stop_timer()
        self.timer_running = True

        def run_timer():
            while self.timer_running and self.timer > 0:
                self.timer_text.value = f"⏰ {self.timer} s"
                self.update()
                time.sleep(1)
                self.timer -= 1
            if self.timer == 0 and self.timer_running:
                self.next_question()

        self.timer_thread = threading.Thread(target=run_timer)
        self.timer_thread.start()

    def stop_timer(self):
        self.timer_running = False
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join()

    def restart_game(self, e=None):
        self.stop_timer()
        self.username_input.visible = True
        self.category_dropdown.visible = True
        self.start_button.visible = True
        self.restart_button.visible = False
        self.question_text.visible = False
        self.timer_text.visible = False
        self.summary_view.visible = False
        self.exit_button.visible = False

        self.question_text.value = "FleTrivia"
        self.question_text.visible = True

        for btn in self.option_buttons:
            btn.visible = False
        self.update()

    def exit_game(self, e=None):
        self.stop_timer()
        self .restart_game()
        self.exit_button.visible = False

def main(page: ft.Page):
    page.title = "FleTrivia"
    page.window.width = 550
    page.window.height = 810
    page.window.resizable = False
    game = TriviaGame()
    page.add(game)

ft.app(target=main)