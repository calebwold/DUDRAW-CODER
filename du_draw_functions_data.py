DU_DRAW_FUNCTIONS = [

    {
        "id": "dudraw.set_canvas_size",
        "description": "Sets the width and height of the drawing canvas in pixels.",
        "syntax": "dudraw.set_canvas_size(width, height)",
        "params": "width (int): The width of the canvas. height (int): The height of the canvas.",
        "example": "dudraw.set_canvas_size(500, 500)",
        "keywords": ["canvas size", "window size", "set dimensions"]
    },
    {
        "id": "dudraw.set_x_scale",
        "description": "Sets the x-axis scale of the drawing canvas.",
        "syntax": "dudraw.set_x_scale(min_x, max_x)",
        "params": "min_x (float/int): The minimum x-value. max_x (float/int): The maximum x-value.",
        "example": "dudraw.set_x_scale(0, 1)",
        "keywords": ["x scale", "set x range", "horizontal scale"]
    },
    {
        "id": "dudraw.set_y_scale",
        "description": "Sets the y-axis scale of the drawing canvas.",
        "syntax": "dudraw.set_y_scale(min_y, max_y)",
        "params": "min_y (float/int): The minimum y-value. max_y (float/int): The maximum y-value.",
        "example": "dudraw.set_y_scale(0, 1)",
        "keywords": ["y scale", "set y range", "vertical scale"]
    },
    {
        "id": "dudraw.set_pen_color",
        "description": "Sets the current pen color using predefined DuDraw colors.",
        "syntax": "dudraw.set_pen_color(color_constant)",
        "params": "color_constant (dudraw.Color): A predefined color constant (e.g., dudraw.YELLOW, dudraw.BLACK, dudraw.WHITE, dudraw.GREEN, dudraw.RED, dudraw.DARK_BLUE, dudraw.DARK_GRAY, dudraw.LIGHT_GRAY).",
        "example": "dudraw.set_pen_color(dudraw.YELLOW)",
        "keywords": ["set color", "pen color", "drawing color"]
    },
    {
        "id": "dudraw.set_pen_color_rgb",
        "description": "Sets the current pen color using RGB values.",
        "syntax": "dudraw.set_pen_color_rgb(r, g, b)",
        "params": "r (int): Red component (0-255). g (int): Green component (0-255). b (int): Blue component (0-255).",
        "example": "dudraw.set_pen_color_rgb(213, 173, 73)",
        "keywords": ["set color rgb", "custom color", "pen color rgb"]
    },
    {
        "id": "dudraw.clear",
        "description": "Clears the entire canvas with a specified background color.",
        "syntax": "dudraw.clear(color_constant)",
        "params": "color_constant (dudraw.Color): A predefined color constant (e.g., dudraw.BLACK, dudraw.WHITE, dudraw.LIGHT_GRAY).",
        "example": "dudraw.clear(dudraw.BLACK)",
        "keywords": ["clear canvas", "background color", "reset drawing"]
    },
    {
        "id": "dudraw.show",
        "description": "Displays the current drawing on the canvas after a specified delay in milliseconds.",
        "syntax": "dudraw.show(delay_ms)",
        "params": "delay_ms (int): Delay in milliseconds before showing the next frame. Use 0 for no delay.",
        "example": "dudraw.show(10)",
        "keywords": ["display", "update canvas", "render", "refresh"]
    },
    {
        "id": "dudraw.dudraw",
        "description": "Initializes a new dudraw object, typically used for more advanced plotting methods.",
        "syntax": "d = dudraw.dudraw()",
        "params": "None.",
        "example": "d = dudraw.dudraw()",
        "keywords": ["initialize dudraw", "dudraw object"]
    },
    {
        "id": "d.fgcolor",
        "description": "Sets the foreground color for plotting using a dudraw object's specific color method.",
        "syntax": "d.fgcolor(r, g, b)",
        "params": "r (int): Red component (0-255). g (int): Green component (0-255). b (int): Blue component (0-255).",
        "example": "d.fgcolor(intensity, intensity, intensity)", # From colorado_elevation
        "keywords": ["foreground color", "plot color"]
    },
    {
        "id": "d.plot",
        "description": "Plots a single pixel at the specified (x, y) coordinates using a dudraw object.",
        "syntax": "d.plot(x, y)",
        "params": "x (int): X coordinate. y (int): Y coordinate.",
        "example": "d.plot(j, i)", # From colorado_elevation
        "keywords": ["draw pixel", "plot point"]
    },
    {
        "id": "d.update",
        "description": "Updates the display for a dudraw object.",
        "syntax": "d.update()",
        "params": "None.",
        "example": "d.update()", # From colorado_elevation
        "keywords": ["update display", "refresh plot"]
    },


    # --- Drawing Primitives ---
    {
        "id": "dudraw.filled_square",
        "description": "Draws a filled square centered at (x, y) with a given half-length.",
        "syntax": "dudraw.filled_square(x, y, half_length)",
        "params": "x (float): X coordinate of the center. y (float): Y coordinate of the center. half_length (float): Half the side length of the square.",
        "example": "dudraw.filled_square(x, WORLD_HEIGHT - y - 1, 1)", # From sand.py (drawing cells)
        "keywords": ["draw square", "filled box", "rectangle"]
    },
    {
        "id": "dudraw.filled_circle",
        "description": "Draws a filled circle centered at (x, y) with a given radius.",
        "syntax": "dudraw.filled_circle(x, y, radius)",
        "params": "x (float): X coordinate of the center. y (float): Y coordinate of the center. radius (float): The radius of the circle.",
        "example": "dudraw.filled_circle(self.pos.x, self.pos.y, self.size)", # From particle systems
        "keywords": ["draw circle", "filled disk", "round shape"]
    },
    {
        "id": "dudraw.line",
        "description": "Draws a straight line between two points (x1, y1) and (x2, y2).",
        "syntax": "dudraw.line(x1, y1, x2, y2)",
        "params": "x1 (float): X coordinate of the start point. y1 (float): Y coordinate of the start point. x2 (float): X coordinate of the end point. y2 (float): Y coordinate of the end point.",
        "example": "dudraw.line(self.pos.x, self.pos.y, self.pos.x + self.vel.x, self.pos.y + self.vel.y)", # From particle systems
        "keywords": ["draw line", "straight line", "connect points"]
    },
    {
        "id": "dudraw.filled_triangle",
        "description": "Draws a filled triangle with three given vertex coordinates.",
        "syntax": "dudraw.filled_triangle(x1, y1, x2, y2, x3, y3)",
        "params": "x1 (float): X coordinate of vertex 1. y1 (float): Y coordinate of vertex 1. x2 (float): X coordinate of vertex 2. y2 (float): Y coordinate of vertex 2. x3 (float): X coordinate of vertex 3. y3 (float): Y coordinate of vertex 3.",
        "example": "dudraw.filled_triangle(0.01, 0, 1, 1, 0.5, 0)", # From wagon_drawing
        "keywords": ["draw triangle", "filled polygon 3"]
    },
    {
        "id": "dudraw.filled_rectangle",
        "description": "Draws a filled rectangle centered at (x, y) with given half-width and half-height.",
        "syntax": "dudraw.filled_rectangle(x, y, half_width, half_height)",
        "params": "x (float): X coordinate of the center. y (float): Y coordinate of the center. half_width (float): Half the width of the rectangle. half_height (float): Half the height of the rectangle.",
        "example": "dudraw.filled_rectangle(car_x, car_y + 0.2, 0.2, 0.05)", # From wagon_drawing
        "keywords": ["draw rectangle", "filled box", "square"]
    },
    # --- Text ---
    {
        "id": "dudraw.set_font_size",
        "description": "Sets the font size for text.",
        "syntax": "dudraw.set_font_size(size)",
        "params": "size (int): The font size in pixels.",
        "example": "dudraw.set_font_size(24)",
        "keywords": ["font size", "text size"]
    },
    {
        "id": "dudraw.text",
        "description": "Draws text centered at (x, y).",
        "syntax": "dudraw.text(x, y, text_string)",
        "params": "x (float): X coordinate of the center. y (float): Y coordinate of the center. text_string (str): The text to draw.",
        "example": "dudraw.text(0.5, 0.5, 'Hello DuDraw')",
        "keywords": ["draw text", "write text", "display message"]
    },
    # --- Mouse and Keyboard Input ---
    {
        "id": "dudraw.mouse_is_pressed",
        "description": "Checks if the mouse button is currently pressed down.",
        "syntax": "dudraw.mouse_is_pressed()",
        "params": "None.",
        "example": "if dudraw.mouse_is_pressed():",
        "keywords": ["mouse pressed", "mouse click status"]
    },
    {
        "id": "dudraw.mouse_x",
        "description": "Returns the current x-coordinate of the mouse cursor.",
        "syntax": "dudraw.mouse_x()",
        "params": "None.",
        "example": "mx = dudraw.mouse_x()",
        "keywords": ["mouse x", "cursor x position"]
    },
    {
        "id": "dudraw.mouse_y",
        "description": "Returns the current y-coordinate of the mouse cursor.",
        "syntax": "dudraw.mouse_y()",
        "params": "None.",
        "example": "my = dudraw.mouse_y()",
        "keywords": ["mouse y", "cursor y position"]
    },
    {
        "id": "dudraw.mouse_position",
        "description": "Returns the current (x, y) coordinates of the mouse cursor.",
        "syntax": "dudraw.mouse_position()",
        "params": "None.",
        "example": "mouse_x, _ = dudraw.mouse_position()",
        "keywords": ["mouse position", "cursor coordinates"]
    },
    {
        "id": "dudraw.mouse_clicked",
        "description": "Checks if the mouse was clicked (pressed and released) in the current frame.",
        "syntax": "dudraw.mouse_clicked()",
        "params": "None.",
        "example": "if dudraw.mouse_clicked():",
        "keywords": ["mouse click event"]
    },
    {
        "id": "dudraw.has_next_key_typed",
        "description": "Checks if a key has been typed (pressed and released) in the current frame.",
        "syntax": "dudraw.has_next_key_typed()",
        "params": "None.",
        "example": "if dudraw.has_next_key_typed():",
        "keywords": ["key typed", "keyboard input"]
    },
    {
        "id": "dudraw.next_key_typed",
        "description": "Returns the character of the next key that was typed.",
        "syntax": "dudraw.next_key_typed()",
        "params": "None.",
        "example": "key = dudraw.next_key_typed()",
        "keywords": ["get key typed", "next key"]
    },
    {
        "id": "dudraw.next_key",
        "description": "Returns the string representation of the next key pressed. (Similar to next_key_typed but might capture more keys).",
        "syntax": "dudraw.next_key()",
        "params": "None.",
        "example": "key = dudraw.next_key()",
        "keywords": ["get key", "next key press"]
    },
    {
        "id": "dudraw.poll",
        "description": "Polls for mouse events, returning x, y coordinates and button status (1 for left click).",
        "syntax": "dudraw.poll()",
        "params": "None.",
        "example": "x, y, button = dudraw.poll()",
        "keywords": ["poll mouse", "mouse event", "get click"]
    },
    {
        "id": "dudraw.key",
        "description": "Checks if any key is currently pressed down.",
        "syntax": "dudraw.key()",
        "params": "None.",
        "example": "if dudraw.key():",
        "keywords": ["key pressed", "any key"]
    },
    {
        "id": "dudraw.enable_keyboard_input",
        "description": "Enables the DuDraw window to receive keyboard input events.",
        "syntax": "dudraw.enable_keyboard_input()",
        "params": "None.",
        "example": "dudraw.enable_keyboard_input()",
        "keywords": ["keyboard enable", "input setup"]
    },
    # DuDraw color constants
    {
        "id": "dudraw.BLACK",
        "description": "Constant for the color black.",
        "syntax": "dudraw.BLACK",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.BLACK)",
        "keywords": ["black color"]
    },
    {
        "id": "dudraw.BLUE",
        "description": "Constant for the color blue.",
        "syntax": "dudraw.BLUE",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.BLUE)",
        "keywords": ["blue color"]
    },
    {
        "id": "dudraw.CYAN",
        "description": "Constant for the color cyan.",
        "syntax": "dudraw.CYAN",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.CYAN)",
        "keywords": ["cyan color"]
    },
    {
        "id": "dudraw.DARK_BLUE",
        "description": "Constant for the color dark blue.",
        "syntax": "dudraw.DARK_BLUE",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.DARK_BLUE)",
        "keywords": ["dark blue color"]
    },
    {
        "id": "dudraw.DARK_GRAY",
        "description": "Constant for the color dark gray.",
        "syntax": "dudraw.DARK_GRAY",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.DARK_GRAY)",
        "keywords": ["dark gray color"]
    },
    {
        "id": "dudraw.GREEN",
        "description": "Constant for the color green.",
        "syntax": "dudraw.GREEN",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.GREEN)",
        "keywords": ["green color"]
    },
    {
        "id": "dudraw.GRAY",
        "description": "Constant for the color gray.",
        "syntax": "dudraw.GRAY",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.GRAY)",
        "keywords": ["gray color"]
    },
    {
        "id": "dudraw.LIGHT_GRAY",
        "description": "Constant for the color light gray.",
        "syntax": "dudraw.LIGHT_GRAY",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.LIGHT_GRAY)",
        "keywords": ["light gray color"]
    },
    {
        "id": "dudraw.MAGENTA",
        "description": "Constant for the color magenta.",
        "syntax": "dudraw.MAGENTA",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.MAGENTA)",
        "keywords": ["magenta color"]
    },
    {
        "id": "dudraw.ORANGE",
        "description": "Constant for the color orange.",
        "syntax": "dudraw.ORANGE",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.ORANGE)",
        "keywords": ["orange color"]
    },
    {
        "id": "dudraw.PINK",
        "description": "Constant for the color pink.",
        "syntax": "dudraw.PINK",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.PINK)",
        "keywords": ["pink color"]
    },
    {
        "id": "dudraw.RED",
        "description": "Constant for the color red.",
        "syntax": "dudraw.RED",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.RED)",
        "keywords": ["red color"]
    },
    {
        "id": "dudraw.WHITE",
        "description": "Constant for the color white.",
        "syntax": "dudraw.WHITE",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.WHITE)",
        "keywords": ["white color"]
    },
    {
        "id": "dudraw.YELLOW",
        "description": "Constant for the color yellow.",
        "syntax": "dudraw.YELLOW",
        "params": "None.",
        "example": "dudraw.set_pen_color(dudraw.YELLOW)",
        "keywords": ["yellow color"]
    },
    # DuDraw Arrow Key Constants
    {
        "id": "dudraw.ARROW_LEFT",
        "description": "Constant for the left arrow key.",
        "syntax": "dudraw.ARROW_LEFT",
        "params": "None.",
        "example": "if key == dudraw.ARROW_LEFT:",
        "keywords": ["arrow left key", "left key"]
    },
    {
        "id": "dudraw.ARROW_RIGHT",
        "description": "Constant for the right arrow key.",
        "syntax": "dudraw.ARROW_RIGHT",
        "params": "None.",
        "example": "if key == dudraw.ARROW_RIGHT:",
        "keywords": ["arrow right key", "right key"]
    },
    {
        "id": "dudraw.ARROW_UP",
        "description": "Constant for the up arrow key.",
        "syntax": "dudraw.ARROW_UP",
        "params": "None.",
        "example": "if key == dudraw.ARROW_UP:",
        "keywords": ["arrow up key", "up key"]
    },
    {
        "id": "dudraw.ARROW_DOWN",
        "description": "Constant for the down arrow key.",
        "syntax": "dudraw.ARROW_DOWN",
        "params": "None.",
        "example": "if key == dudraw.ARROW_DOWN:",
        "keywords": ["arrow down key", "down key"]
    }
]
