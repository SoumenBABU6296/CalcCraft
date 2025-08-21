import os # Import os for path operations
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.clipboard import Clipboard
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.core.text import Label as CoreLabel
from asteval import Interpreter
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.metrics import dp, sp
import re
class CopyOnlyTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.readonly = False              
        self.use_handles = True            
        self.password = False              

    def keyboard_on_request(self, *args):
        return None

    def insert_text(self, substring, from_undo=False):
        pass

    def do_backspace(self, from_undo=False, mode='bkspc'):
        pass

    def paste(self, *args):
        pass
    
class NoKeyboardTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.readonly = False
        self.use_handles = True
        self.password = False

    def keyboard_on_request(self, *args):
        return None

    def do_backspace(self, from_undo=False, mode='bkspc'):
        pass
        
    def cut(self, data=''):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            raw_cursor_index = self.get_cursor_from_xy(*touch.pos)

            if isinstance(raw_cursor_index, (tuple, list)):
                cursor_index = raw_cursor_index[0] 
            elif isinstance(raw_cursor_index, int):
                cursor_index = raw_cursor_index
            else:
                cursor_index = 0

            text_len = len(self.text)
            cursor_index = max(0, min(cursor_index, text_len))

            if touch.is_double_tap:
                if cursor_index is not None:
                    start_index, end_index = self._find_word_boundaries(cursor_index)
                    self.select_text(start_index, end_index)
                return True
            else:
                if self.selection_text:
                    self.select_text(cursor_index, cursor_index) 
                    return True 
                
                self.cursor = self.get_cursor_from_index(cursor_index)
                self.cursor_index = cursor_index
                
                Clock.schedule_once(lambda dt: self.select_text(self.cursor_index, self.cursor_index), 0.1)
                
                return True

        if self.selection_text:
            self.select_text(self.cursor_index, self.cursor_index)
            return super().on_touch_down(touch) 

        return super().on_touch_down(touch)

    def copy(self, data=''):
        super().copy(data)
        self.select_text(self.cursor_index, self.cursor_index)

    def _find_word_boundaries(self, index):
        text = self.text
        text_len = len(text)

        if not text_len:
            return 0, 0

        start = index
        while start > 0 and not re.match(r'\s|\W', text[start - 1]):
            start -= 1

        end = index
        while end < text_len and not re.match(r'\s|\W', text[end]):
            end += 1

        return start, end
class NeonButton(Button):
    def __init__(self, **kwargs):
        super(NeonButton, self).__init__(**kwargs)
        with self.canvas.before:
            Color(0, 1, 0, 1)  # Neon Cyan.....................
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(15)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class main(App):
    def build(self):
        self.icon = "Calculato_Icon.jpg"
        self.operators = ["÷", "×", "+", "—", "^","%","("]
        self.dot = ["."]
        self.digit = [str(i) for i in range(10)]
        self.check_op = [str(element) for element in self.operators]
        self.last_was_operator = None
        self.last_button = None
        self.last_was_dot = None
        self.i = 0
        self.Bracket = 0
        self.final = -1
        self.error_flag = 0
        self.dot_flag = 1
        self.stack = []
        self.error_text = ""
        self.aeval = Interpreter()
        self.base_font_size = sp(72)
        self.result_base_font_size = sp(45)
        self.min_font_size = sp(18)
        main_layout = BoxLayout(orientation="vertical")

        self.blank = TextInput(
            background_color=(0, 0,0, 1),
            foreground_color="cyan",
            multiline=False,
            halign="right",
            font_size=self.base_font_size,
            readonly=True,
            size_hint=(1, None),
            height=dp(15)
        )
        main_layout.add_widget(self.blank)

        self.solution = NoKeyboardTextInput(
            background_color=(0, 0,0, 1),
            foreground_color="cyan",
            multiline=False,
            halign="right",
            font_size=self.base_font_size,
            readonly=False,
            size_hint=(1, None),
            height=dp(170)
        )
        main_layout.add_widget(self.solution)
    
        self.result = CopyOnlyTextInput(
            background_color=(0, 0,0, 1),
            foreground_color=(1.0, 1.0, 0.878, 0.7),
            multiline=False,
            halign="right",
            font_size=self.base_font_size,
            readonly=True,
            size_hint=(1, None),
            height=dp(100)
        )
        main_layout.add_widget(self.result)

        buttons = [
            ["^", "(", ")", "%", "AC"],
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "+"],
            [".", "0", "DEL", "—"]
        ]

        mode_settings_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(42))

        self.History_button = NeonButton(
            text= "His",
            font_size= sp(25),
            color=(1, 1, 1, 1),
            size_hint=(0.5, 1),
            background_color=(1, 0.2, 0.1, 1)
        )
        self.History_button.bind(on_press = self.on_History_press)

        self.settings_button = NeonButton(
            text="SP",
            font_size=sp(25),
            color=(1, 1, 1, 1),
            background_color= (0.2, 0.9, 1, 1)
        )
        #self.settings_button.bind(on_press=self.on_settings_press)

        self.mode_button = NeonButton(
            text="Mode",
            font_size=sp(25),
            color=(1, 1, 1, 1),
            background_normal = '',
            background_color=(1, 0.2, 0, 1)
        )
        #self.mode_button.bind(on_press=self.on_mode_toggle)
        mode_settings_layout.add_widget(self.History_button)
        mode_settings_layout.add_widget(self.settings_button)
        mode_settings_layout.add_widget(self.mode_button)
        main_layout.add_widget(mode_settings_layout)

        for row in buttons:
            h_layout = BoxLayout()
            for label in row:
                font_size = sp(32)
                btn_background_clr = (0.7, 0.5, 0.2, 1)
                if label in self.operators and label != "(":
                    font_size = sp(50)
                elif label in self.digit or label == '.' or label == 'DEL':
                    btn_background_clr = (0.5, 0.5, 0.5, 1)
                elif label == 'AC':
                    btn_background_clr = (0.6, 0.3, 0.1, 1)
                button = NeonButton(
                    text=label,
                    font_size=font_size,
                    color=(1, 1, 1, 1),
                    background_color = btn_background_clr
                )
                button.bind(on_press=self.on_button_press)
                h_layout.add_widget(button)
            main_layout.add_widget(h_layout)

        equal_button = NeonButton(
            text="=",
            font_size=sp(65),
            color=(0, 0.7, 1, 1),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        equal_button.bind(on_press=self.final_result)
        main_layout.add_widget(equal_button)
        return main_layout
    
    
    def get_history_file_path(self):
        
        app_data_dir = self.user_data_dir 
        history_filename = "history.txt"
        history_path = os.path.join(app_data_dir, history_filename)

        # Check if history.txt exists in user_data_dir (where we want to read/write)
        if not os.path.exists(history_path):
            source_path_in_app = os.path.join(self.directory, history_filename)
            if os.path.exists(source_path_in_app):
                try:
                    with open(source_path_in_app, 'r') as f_in:
                        content = f_in.read()
                    with open(history_path, 'w') as f_out:
                        f_out.write(content)
                except Exception as e:
                    print(f"Error copying history.txt from app resources: {e}")
            else:
                try:
                    with open(history_path, 'w') as f_out:
                        f_out.write("") # Create an empty file
                except Exception as e:
                    print(f"Error creating empty history.txt: {e}")
        
        return history_path

    def add_to_history(self, expression, result):
        history_file_path = self.get_history_file_path()
        with open(history_file_path, "a") as file: 
            if expression.startswith("="):
                expression = expression[1:].strip()
                file.write(f"{expression} = \n{result}\n\n")
            else:
                file.write(f"{expression} = \n{result}\n\n")

    def on_History_press(self, instance):
        history_file_path = self.get_history_file_path() 
        try:
            with open(history_file_path, "r") as file: 
                history = file.read()
        except FileNotFoundError:
            history = "No history available."
        except Exception as e:
            history = f"Error reading history: {e}" 

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        history_input = CopyOnlyTextInput(
            text=history,
            readonly=True,
            font_size=sp(20),
            size_hint=(1, None),
            background_color=(0, 0, 0, 0),
            foreground_color=(1, 1, 1, 1),
            cursor_blink=False,
        )

        history_input.bind(minimum_height=history_input.setter('height'))
        history_input.bind(text=lambda instance, value: instance._refresh_text())

        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll_view.add_widget(history_input)
        
        button_layout = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))
        clear_button = Button(text="Clear")
        close_button = Button(text="Close")
        button_layout.add_widget(clear_button)
        button_layout.add_widget(close_button)

        content.add_widget(scroll_view)
        content.add_widget(button_layout)
        popup = Popup(
            title="Calculation History",
            content=content,
            size_hint=(0.9, 0.6),
            auto_dismiss=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.4}
        )
        def on_clear_press(instance):
            history_file_path = self.get_history_file_path() 
            try:
                with open(history_file_path, "w") as file: 
                    file.write("")
                popup.dismiss() 
                self.on_History_press(None) 
            except Exception as e:
                print(f"Error clearing history file: {e}")

        clear_button.bind(on_press=on_clear_press)
        close_button.bind(on_press=popup.dismiss)
        popup.open()


    def adjust_font_size(self):
        text = self.solution.text
        font_size = self.base_font_size
        max_width = self.solution.width - dp(40)

        while font_size >= self.min_font_size:
            label = CoreLabel(text=text, font_size=font_size)
            label.refresh()
            text_width = label.texture.size[0]

            if text_width <= max_width:
                break
            font_size -= sp(2)
        self.solution.font_size = font_size

    def adjust_result_font_size(self):
        text = self.result.text
        font_size = self.result_base_font_size
        max_width = self.result.width - dp(30)

        while font_size >= self.min_font_size:
            label = CoreLabel(text=text, font_size=font_size)
            label.refresh()
            text_width = label.texture.size[0]

            if text_width <= max_width:
                break
            font_size -= sp(2)
        self.result.font_size = font_size

    def on_button_press(self, instance):
        current = self.solution.text
        button_text = instance.text

        if button_text == 'AC':
            self.last_button = "0"
            self.last_was_operator = None
            self.last_was_dot = None
            self.i = 0
            self.final = -1
            self.solution.text = "0"
            self.result.text = "" 
            self.dot_flag = 1
            self.error_flag = 0
            self.stack.clear()
        elif button_text == 'DEL':
            if(self.solution.text != "0"):
                text = self.solution.text
                new_text = ""
                if text:
                    last_char = text[-1]
                    if "=" in text:
                        if text.strip()[-2] == " ":
                            self.solution.text = "0"
                        else:
                            self.solution.text = text[:-1]
                    new_text = text[:-1]
                    if last_char == '(':
                        if self.stack:
                            self.stack.pop()
                    elif last_char == ')':
                        self.stack.append('(')
                    if self.solution.text.strip() == "":
                        self.solution.text = "0"
                        self.last_was_operator = None
                    elif self.solution.text == "0":
                        return
                    else:
                        self.solution.text = new_text
                    if last_char == ".":
                        self.dot_flag = 1
                    if last_char in self.operators:
                        self.dot_flag = 0
                    if self.solution.text.strip():
                        self.last_button = self.solution.text[-1]
                        self.last_was_operator = self.last_button in self.operators
                        self.last_was_dot = self.last_button in self.dot
                    else:
                        self.last_button = "0"
                        self.last_was_operator = None
                        self.last_was_dot = None
                    ##############################################
                    if new_text and new_text[-1] in self.operators and new_text[-1] !="%":
                        self.result.text = ""
                    elif any(op in self.solution.text for op in self.check_op):
                        temp_solution_text = self.solution.text
                        calculated_result = self.on_solution(None)
                        if "Error" in calculated_result: 
                            self.result.text = calculated_result
                            self.error_flag = 1 
                        else:
                            self.result.text = calculated_result
                            self.error_flag = 0
                        self.adjust_result_font_size()
                    else:
                        self.result.text = ""
                else:
                    self.solution.text = "0"
                    self.result.text = "" 
                    self.last_was_operator = None
                    self.last_button = "0"
            else:
                self.last_button = "0"

        elif button_text == '(':
            self.stack.append('(')
            if current == "0" and button_text in ["("]:
                self.solution.text = '('
            else:
                self.solution.text += '('
        elif button_text == ')':
            if self.stack:
                self.stack.pop()
                self.solution.text += ')'
        else:
            if current == "0" and button_text in self.operators and button_text != "—":
                return
            elif current == "" and button_text in self.operators and button_text != "—":
                return
            elif current and button_text in self.operators and self.solution.text[-1] == "%":
                self.solution.text += button_text
                if button_text in self.operators and button_text != "%":
                    self.result.text = ""
                else:
                    calculated_result = self.on_solution(None)
                    if "Error" in calculated_result:
                        self.result.text = calculated_result
                        self.error_flag = 1 
                    else:
                        self.result.text = calculated_result
                        self.error_flag = 0 
                    self.adjust_result_font_size()

            elif  button_text in self.operators and button_text !="—" and self.solution.text[-1] == '(':
                return
            elif current and (self.last_was_operator and button_text in self.operators):
                return
            elif self.last_was_dot and button_text in self.dot:
                return
            elif current and (self.last_was_dot and button_text in self.operators):
                return
            elif self.dot_flag == 0 and button_text in self.dot:
                return
            else:
                if current == "0" and button_text.isdigit():
                    self.solution.text = button_text
                elif current == "0" and button_text in ["—", "("]:
                    self.solution.text = button_text
                elif current == "" and button_text in ["—", "("]:
                    self.solution.text = button_text
                else:
                    new_text = current + button_text
                    self.solution.text = new_text
                    self.i += 1
                    if (button_text in self.operators) or ("." not in self.solution.text):
                        self.dot_flag = 1
                    if (button_text in self.dot) and ("." in self.solution.text):
                        self.dot_flag = 0
                self.last_button = self.solution.text[-1]
                self.last_was_operator = self.last_button in self.operators
                self.last_was_dot = self.last_button in self.dot
                if any(op in self.solution.text for op in self.check_op) and (button_text == "%" or button_text.isdigit() or button_text == ")"):
                    temp_solution_text = self.solution.text
                    calculated_result = self.on_solution(None)
                    if "Error" in calculated_result:
                        self.result.text = calculated_result
                        self.error_flag = 1 
                    else:
                        self.result.text = calculated_result
                        self.error_flag = 0 
                    self.adjust_result_font_size()
                else:
                    self.result.text = "" 
        self.adjust_font_size()

    def on_solution(self, instance=None):
        text = self.solution.text
        if text.startswith("="):
            text = text[1:].strip()
        if text:
            if self.stack:
                length = len(self.stack)
                while length != 0:
                    text += ')'
                    length -=1
            try:
                while re.search(r'(\(?[\d\+\-\*\/\(\)]+\)?)(%+)', text):
                    text = re.sub(r'(\(?[\d\+\-\*\/\(\)]+\)?)(%+)', lambda m: '(' + m.group(1) + '/100' * len(m.group(2)) + ')', text)
                text = re.sub(r'\((\s*|\(*\s*\)*)\)',"", text)
                text = re.sub(r'(\([^\(\)]+\))%', r'(\1/100)', text)
                text = re.sub(r'\b0+(\d+)', r'\1', text)
                text = re.sub(r'(\d|\))\(', r'\1*(', text)
                text = re.sub(r'\)(\d)', r')*\1', text)
                text = text.replace("^", "**").replace("×", "*").replace("÷", "/").replace("—", "-")
                #print(f"Attempting to evaluate: '{text}'")
                result = eval(text)
                return str(result)
            except ZeroDivisionError:
                self.error_text = self.solution.text 
                self.error_flag = 1
                return "Error: Cannot divide by zero." 
            except Exception as e:
                self.error_text = self.solution.text 
                self.error_flag = 1
                return f"Error: {str(e)}" 
        self.adjust_font_size()
        return "" 
    ###################
    def final_result(self,instance):
        text = self.solution.text
        calculated_result = self.on_solution(None)
        self.result.text = ""
        self.stack.clear()
        if "Error" in calculated_result: 
            self.solution.text = calculated_result
            self.error_flag = 1 
        else:
            self.solution.text = "= "+calculated_result
            self.error_flag = 0
            self.add_to_history(text,calculated_result)
        self.adjust_font_size()
        

    def on_mode_toggle(self, instance):
        current_color = self.mode_button.background_color
        if current_color == (1, 0, 0, 1):
            self.mode_button.background_color = (0, 1, 0, 1)
        else:
            self.mode_button.background_color = (1, 0, 0, 1)
    def on_settings_press(self, instance):
        print("Settings button pressed!")

if __name__ == "__main__":
    main().run()