import tkinter as tk
import sys
from pathlib import Path
from PIL import Image, ImageTk


# ==================================================
# FILE PATHS
# ==================================================

maya_path = Path(__file__).parent / "assets" / "Maya_image.jpeg"


# ==================================================
# CONNECT TO HIDDEN HEMERA FILES
# ==================================================

hidden_folder = Path(__file__).parent.parent / "hidden"
sys.path.append(str(hidden_folder))

from hemera_reference import profile_A, profile_B
from oracle_security import check_access


# ==================================================
# MAIN WINDOW
# ==================================================

root = tk.Tk()
root.title("ORACLE // HEMERA DATABASE")
root.geometry("1000x760")


# ==================================================
# FONTS
# ==================================================

FONT = ("Courier New", 12)
FONT_BOLD = ("Courier New", 12, "bold")
TITLE_FONT = ("Courier New", 24, "bold")
SUBTITLE_FONT = ("Courier New", 13)


# ==================================================
# GLOBAL VARIABLES
# ==================================================

crime_sample = []
matched_profile = None
A_matches = 0
B_matches = 0


# ==================================================
# SCROLLABLE AREA
# ==================================================

main_canvas = tk.Canvas(root)

scrollbar = tk.Scrollbar(
    root,
    orient="vertical",
    command=main_canvas.yview
)

scrollable_frame = tk.Frame(main_canvas)


def update_scroll_region(event=None):

    main_canvas.configure(
        scrollregion=main_canvas.bbox("all")
    )


scrollable_frame.bind(
    "<Configure>",
    update_scroll_region
)


canvas_window = main_canvas.create_window(
    (0, 0),
    window=scrollable_frame,
    anchor="nw"
)


def resize_frame(event):

    main_canvas.itemconfig(
        canvas_window,
        width=event.width
    )


main_canvas.bind(
    "<Configure>",
    resize_frame
)


main_canvas.configure(
    yscrollcommand=scrollbar.set
)


main_canvas.pack(
    side="left",
    fill="both",
    expand=True
)


scrollbar.pack(
    side="right",
    fill="y"
)


# ==================================================
# MOUSE WHEEL SCROLLING
# ==================================================

def on_mousewheel(event):

    main_canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


main_canvas.bind_all(
    "<MouseWheel>",
    on_mousewheel
)


# ==================================================
# UTILITY FUNCTIONS
# ==================================================

def clear_screen():

    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    main_canvas.yview_moveto(0)


def title(text, subtitle=None):

    tk.Label(
        scrollable_frame,
        text=text,
        font=TITLE_FONT
    ).pack(
        pady=(30, 5)
    )

    if subtitle:

        tk.Label(
            scrollable_frame,
            text=subtitle,
            font=SUBTITLE_FONT
        ).pack(
            pady=(0, 20)
        )


def scroll_to_bottom():

    root.update_idletasks()

    main_canvas.configure(
        scrollregion=main_canvas.bbox("all")
    )

    main_canvas.yview_moveto(1.0)


# ==================================================
# STAGE 1 — ACCESS
# ==================================================

def show_access():

    clear_screen()

    title(
        "ORACLE // HEMERA",
        "CONFIDENTIAL RESEARCH DATABASE"
    )


    tk.Label(
        scrollable_frame,
        text="ENTER ACCESS CODE",
        font=FONT_BOLD
    ).pack(
        pady=(60, 10)
    )


    access_entry = tk.Entry(
        scrollable_frame,
        width=30,
        font=("Courier New", 15),
        justify="center"
    )

    access_entry.pack(
        pady=10
    )


    status = tk.Label(
        scrollable_frame,
        text="",
        font=FONT
    )

    status.pack(
        pady=10
    )


    def attempt_access():

        code = access_entry.get().strip()

        if check_access(code):

            status.config(
                text=(
                    "ACCESS GRANTED\n"
                    "HEMERA DATABASE CONNECTED"
                )
            )

            root.after(
                1500,
                show_profile_input
            )

        else:

            status.config(
                text="ACCESS DENIED"
            )


    tk.Button(
        scrollable_frame,
        text="UNLOCK ORACLE",
        command=attempt_access,
        font=FONT_BOLD,
        width=20
    ).pack(
        pady=15
    )


# ==================================================
# STAGE 2 — CRIME-SCENE PROFILE INPUT
# ==================================================

def show_profile_input():

    clear_screen()

    title(
        "CRIME-SCENE PROFILE",
        "INPUT REQUIRED"
    )


    tk.Label(
        scrollable_frame,
        text=(
            "During the previous investigation, you recovered\n"
            "the genetic profile of the biological trace found\n"
            "in Professor X's laboratory.\n\n"
            "Enter that profile below."
        ),
        font=FONT,
        justify="center"
    ).pack(
        pady=20
    )


    tk.Label(
        scrollable_frame,
        text="Enter the 20 markers separated by spaces:",
        font=FONT_BOLD
    ).pack(
        pady=10
    )


    profile_entry = tk.Entry(
        scrollable_frame,
        width=75,
        font=("Courier New", 12),
        justify="center"
    )

    profile_entry.pack(
        pady=10
    )


    tk.Label(
        scrollable_frame,
        text=(
            "Example format:\n"
            "AG CC TG AA CT GG TT AC CG GA "
            "CC AT TG GG AC CT AA GC TT CG"
        ),
        font=("Courier New", 10),
        justify="center"
    ).pack(
        pady=5
    )


    status = tk.Label(
        scrollable_frame,
        text="",
        font=FONT
    )

    status.pack(
        pady=10
    )


    def submit_profile():

        global crime_sample

        crime_sample = (
            profile_entry
            .get()
            .strip()
            .upper()
            .split()
        )


        if len(crime_sample) != 20:

            status.config(
                text=(
                    "ERROR:\n"
                    "ORACLE expects exactly "
                    "20 genetic markers."
                )
            )

            return


        status.config(
            text="PROFILE ACCEPTED"
        )


        root.after(
            1000,
            show_code_challenge
        )


    tk.Button(
        scrollable_frame,
        text="LOAD PROFILE",
        command=submit_profile,
        font=FONT_BOLD,
        width=20
    ).pack(
        pady=15
    )


# ==================================================
# STAGE 3 — PYTHON CHALLENGE
# ==================================================

def show_code_challenge():

    clear_screen()

    title(
        "GENETIC PROFILE ANALYSIS",
        "COMPLETE PROFESSOR X'S CODE"
    )


    tk.Label(
        scrollable_frame,
        text=(
            "ORACLE contains two anonymous HEMERA reference profiles.\n"
            "Your crime-scene profile must be compared with them\n"
            "marker by marker."
        ),
        font=FONT,
        justify="center"
    ).pack(
        pady=10
    )


    logic_frame = tk.LabelFrame(
        scrollable_frame,
        text="WHAT SHOULD THE PROGRAM DO?",
        font=FONT_BOLD,
        padx=20,
        pady=15
    )

    logic_frame.pack(
        fill="x",
        padx=70,
        pady=15
    )


    tk.Label(
        logic_frame,
        text=(
            "1. Examine each marker position.\n"
            "2. Compare the crime-scene marker with the reference marker.\n"
            "3. If the two markers are identical, increase the match counter by one."
        ),
        font=FONT,
        justify="left"
    ).pack(
        anchor="w"
    )


    reference_frame = tk.LabelFrame(
        scrollable_frame,
        text="PYTHON REFERENCE",
        font=FONT_BOLD,
        padx=20,
        pady=15
    )

    reference_frame.pack(
        fill="x",
        padx=70,
        pady=10
    )


    tk.Label(
        reference_frame,
        text=(
            "==    checks whether two values are equal\n"
            "+     performs addition\n"
            "len(x) gives the number of elements in x\n"
            "sample[i] gives the element at position i"
        ),
        font=FONT,
        justify="left"
    ).pack(
        anchor="w"
    )


    code_frame = tk.LabelFrame(
        scrollable_frame,
        text="INCOMPLETE ANALYSIS",
        font=FONT_BOLD,
        padx=20,
        pady=15
    )

    code_frame.pack(
        fill="x",
        padx=70,
        pady=15
    )


    line1 = tk.Frame(
        code_frame
    )

    line1.pack(
        pady=8
    )


    tk.Label(
        line1,
        text="if sample[i]",
        font=FONT
    ).pack(
        side="left"
    )


    operator_entry = tk.Entry(
        line1,
        width=6,
        font=FONT,
        justify="center"
    )

    operator_entry.pack(
        side="left",
        padx=10
    )


    tk.Label(
        line1,
        text="profile[i]:",
        font=FONT
    ).pack(
        side="left"
    )


    line2 = tk.Frame(
        code_frame
    )

    line2.pack(
        pady=8
    )


    tk.Label(
        line2,
        text="matches = matches +",
        font=FONT
    ).pack(
        side="left"
    )


    counter_entry = tk.Entry(
        line2,
        width=6,
        font=FONT,
        justify="center"
    )

    counter_entry.pack(
        side="left",
        padx=10
    )


    status = tk.Label(
        scrollable_frame,
        text="",
        font=FONT
    )

    status.pack(
        pady=10
    )


    def run_analysis():

        operator = operator_entry.get().strip()
        increment = counter_entry.get().strip()


        if operator != "==":

            status.config(
                text=(
                    "CODE ERROR:\n"
                    "How should Python check whether "
                    "two values are equal?"
                )
            )

            return


        if increment != "1":

            status.config(
                text=(
                    "CODE ERROR:\n"
                    "How much should the counter increase "
                    "for one matching marker?"
                )
            )

            return


        perform_comparison()


    tk.Button(
        scrollable_frame,
        text="RUN ANALYSIS",
        command=run_analysis,
        font=FONT_BOLD,
        width=20
    ).pack(
        pady=(10, 30)
    )


# ==================================================
# STAGE 4 — PROFILE COMPARISON
# ==================================================

def perform_comparison():

    global A_matches
    global B_matches
    global matched_profile


    A_matches = 0
    B_matches = 0


    for i in range(len(crime_sample)):

        if crime_sample[i] == profile_A[i]:
            A_matches += 1

        if crime_sample[i] == profile_B[i]:
            B_matches += 1


    if A_matches > B_matches:

        matched_profile = "A"

    elif B_matches > A_matches:

        matched_profile = "B"

    else:

        matched_profile = None


    show_results()


# ==================================================
# STAGE 5 — RESULTS
# ==================================================

def show_results():

    clear_screen()

    title(
        "ANALYSIS COMPLETE"
    )


    output = tk.Label(
        scrollable_frame,
        text="Analyzing genetic markers...",
        font=("Courier New", 14),
        justify="center"
    )

    output.pack(
        pady=60
    )


    def show_A():

        output.config(
            text=f"Profile A: {A_matches}/20 matches"
        )


    def show_B():

        output.config(
            text=(
                f"Profile A: {A_matches}/20 matches\n\n"
                f"Profile B: {B_matches}/20 matches"
            )
        )


    def show_match():

        if matched_profile is None:

            output.config(
                text="RESULT INCONCLUSIVE"
            )

            return


        output.config(
            text=(
                f"Profile A: {A_matches}/20 matches\n\n"
                f"Profile B: {B_matches}/20 matches\n\n"
                f"MATCH FOUND: PROFILE {matched_profile}"
            )
        )


    def show_encrypted():

        if matched_profile is None:
            return


        output.config(
            text=(
                f"Profile A: {A_matches}/20 matches\n\n"
                f"Profile B: {B_matches}/20 matches\n\n"
                f"MATCH FOUND: PROFILE {matched_profile}\n\n"
                "AUTOMATED GENETIC COMPARISON COMPLETE\n\n"
                "IDENTITY RECORD REMAINS ENCRYPTED\n\n"
                "Manual statistical validation required."
            )
        )


        tk.Button(
            scrollable_frame,
            text="BEGIN STATISTICAL VALIDATION",
            command=show_probability,
            font=FONT_BOLD
        ).pack(
            pady=20
        )


    root.after(1500, show_A)
    root.after(2800, show_B)
    root.after(4500, show_match)
    root.after(6500, show_encrypted)


# ==================================================
# STAGE 6 — PROBABILITY
# ==================================================

def show_probability():

    clear_screen()

    title(
        "MANUAL STATISTICAL VALIDATION"
    )


    tk.Label(
        scrollable_frame,
        text=(
            "Professor X configured ORACLE to require\n"
            "independent statistical confirmation before\n"
            "revealing confidential personnel identities."
        ),
        font=FONT,
        justify="center"
    ).pack(
        pady=15
    )


    probability_frame = tk.LabelFrame(
        scrollable_frame,
        text="STATISTICAL CHALLENGE",
        font=FONT_BOLD,
        padx=25,
        pady=20
    )

    probability_frame.pack(
        fill="x",
        padx=70,
        pady=20
    )


    tk.Label(
        probability_frame,
        text=(
            "ORACLE detected a 20/20 marker match.\n\n"
            "For the purpose of this analysis:\n\n"
            "n = 20\n"
            "p = 0.5\n\n"
            "Calculate the probability that an unrelated individual\n"
            "would match ALL 20 markers by chance.\n\n"
            "Calculate:\n"
            "P(X = 20)"
        ),
        font=FONT,
        justify="left"
    ).pack(
        anchor="w"
    )


    format_frame = tk.LabelFrame(
        scrollable_frame,
        text="ANSWER FORMAT",
        font=FONT_BOLD,
        padx=25,
        pady=15
    )

    format_frame.pack(
        fill="x",
        padx=70,
        pady=10
    )


    tk.Label(
        format_frame,
        text=(
            "Round the coefficient to 2 digits after the decimal point.\n\n"
            "If your answer is written in scientific notation,\n"
            "enter it using e notation.\n\n"
            "Example:\n"
            "3.276 x 10^-5  ->  3.28e-5"
        ),
        font=FONT,
        justify="left"
    ).pack(
        anchor="w"
    )


    tk.Label(
        scrollable_frame,
        text="ENTER CALCULATED PROBABILITY:",
        font=FONT_BOLD
    ).pack(
        pady=(20, 5)
    )


    probability_entry = tk.Entry(
        scrollable_frame,
        width=25,
        font=("Courier New", 14),
        justify="center"
    )

    probability_entry.pack(
        pady=10
    )


    status = tk.Label(
        scrollable_frame,
        text="",
        font=FONT
    )

    status.pack(
        pady=10
    )


    def validate():

        try:

            entered = float(
                probability_entry.get()
            )

        except ValueError:

            status.config(
                text=(
                    "INPUT ERROR:\n"
                    "Enter a numerical probability.\n"
                    "Example: 3.28e-5"
                )
            )

            return


        correct_probability = 9.5367431640625e-7

        tolerance = correct_probability * 0.05


        if abs(entered - correct_probability) <= tolerance:

            status.config(
                text="STATISTICAL VALIDATION ACCEPTED"
            )

            root.after(
                1200,
                show_identity
            )

        else:

            status.config(
                text=(
                    "STATISTICAL VALIDATION FAILED\n\n"
                    "Check your binomial calculation and rounding."
                )
            )


    tk.Button(
        scrollable_frame,
        text="VALIDATE",
        command=validate,
        font=FONT_BOLD,
        width=20
    ).pack(
        pady=(10, 40)
    )


# ==================================================
# STAGE 7 — IDENTITY REVEAL
# ==================================================

def show_identity():

    clear_screen()

    title(
        "STATISTICAL VALIDATION ACCEPTED"
    )


    decrypt_label = tk.Label(
        scrollable_frame,
        text="Decrypting personnel record...",
        font=("Courier New", 15),
        justify="center"
    )

    decrypt_label.pack(
        pady=(40, 20)
    )


    identity_frame = tk.Frame(
        scrollable_frame
    )


    record_label = tk.Label(
        identity_frame,
        text="",
        font=("Courier New", 15, "bold"),
        justify="center"
    )


    name_label = tk.Label(
        identity_frame,
        text="",
        font=("Courier New", 22, "bold"),
        justify="center"
    )


    role_label = tk.Label(
        identity_frame,
        text="",
        font=("Courier New", 14),
        justify="center"
    )


    maya_image_label = tk.Label(
        identity_frame
    )


    final_message_label = tk.Label(
        scrollable_frame,
        text="",
        font=("Courier New", 13),
        justify="center"
    )


    # ==================================================
    # REVEAL IDENTITY
    # ==================================================

    def reveal_identity():

        decrypt_label.config(
            text=""
        )


        identity_frame.pack(
            pady=10
        )


        if matched_profile == "A":

            # ------------------------------------------
            # PERSONNEL RECORD FIRST
            # ------------------------------------------

            record_label.config(
                text=(
                    "------------------------------------\n"
                    "PERSONNEL RECORD UNLOCKED\n"
                    "------------------------------------\n\n"
                    "PROFILE A"
                )
            )

            record_label.pack(
                pady=(5, 15)
            )


            # ------------------------------------------
            # NAME SECOND
            # ------------------------------------------

            name_label.config(
                text="MAYA"
            )

            name_label.pack(
                pady=(5, 2)
            )


            # ------------------------------------------
            # ROLE THIRD
            # ------------------------------------------

            role_label.config(
                text="PhD Researcher 2"
            )

            role_label.pack(
                pady=(0, 15)
            )


            # ------------------------------------------
            # IMAGE AFTER NAME/ROLE
            # ------------------------------------------

            try:

                image = Image.open(
                    maya_path
                )


                image.thumbnail(
                    (260, 260)
                )


                maya_photo = ImageTk.PhotoImage(
                    image
                )


                maya_image_label.config(
                    image=maya_photo
                )


                maya_image_label.image = maya_photo


                maya_image_label.pack(
                    pady=(5, 20)
                )


            except Exception as error:

                maya_image_label.config(
                    text=(
                        "[ Maya image could not be loaded ]\n\n"
                        f"Expected file:\n{maya_path}\n\n"
                        f"Error:\n{error}"
                    ),
                    font=("Courier New", 10)
                )

                maya_image_label.pack(
                    pady=10
                )


        elif matched_profile == "B":

            record_label.config(
                text=(
                    "------------------------------------\n"
                    "PERSONNEL RECORD UNLOCKED\n"
                    "------------------------------------\n\n"
                    "PROFILE B"
                )
            )

            record_label.pack(
                pady=(10, 15)
            )


            name_label.config(
                text="MASTER INTERN"
            )

            name_label.pack(
                pady=(5, 2)
            )


            role_label.config(
                text="HEMERA Personnel Record"
            )

            role_label.pack(
                pady=(0, 20)
            )


        else:

            record_label.config(
                text="PERSONNEL RECORD UNAVAILABLE"
            )

            record_label.pack(
                pady=10
            )


            name_label.config(
                text="UNKNOWN"
            )

            name_label.pack(
                pady=5
            )


        # Final clue comes BELOW everything
        final_message_label.pack(
            pady=(25, 40)
        )


        scroll_to_bottom()


    # ==================================================
    # IDENTIFICATION COMPLETE
    # ==================================================

    def identification_complete():

        final_message_label.config(
            text=(
                "IDENTIFICATION COMPLETE\n\n"
                "One final piece of evidence remains."
            )
        )

        scroll_to_bottom()


    # ==================================================
    # FINAL EVIDENCE BOX
    # ==================================================

    def evidence_box():

        final_message_label.config(
            text=(
                "IDENTIFICATION COMPLETE\n\n"
                "One final piece of evidence remains.\n\n"
                "Professor X did not trust the laboratory network\n"
                "with everything.\n\n"
                "Locate the locked HEMERA evidence box."
            )
        )

        scroll_to_bottom()


    # ==================================================
    # BOX CODE
    # ==================================================

    def reveal_box_code():

        final_message_label.config(
            text=(
                "IDENTIFICATION COMPLETE\n\n"
                "One final piece of evidence remains.\n\n"
                "Professor X did not trust the laboratory network\n"
                "with everything.\n\n"
                "Locate the locked HEMERA evidence box.\n\n"
                "BOX ACCESS CODE:\n\n"
                "7 3 1 4\n\n"
                "Recover the final evidence and "
                "complete the investigation."
            )
        )

        scroll_to_bottom()


    # ==================================================
    # TIMING
    # ==================================================

    root.after(
        2000,
        reveal_identity
    )


    root.after(
        5000,
        identification_complete
    )


    root.after(
        7500,
        evidence_box
    )


    root.after(
        10000,
        reveal_box_code
    )


# ==================================================
# START
# ==================================================

show_access()

root.mainloop()