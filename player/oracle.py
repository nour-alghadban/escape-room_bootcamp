import tkinter as tk
import sys
from pathlib import Path
from PIL import Image, ImageTk

import re
import shutil
import platform
import subprocess

# ==================================================
# FILE PATHS
# ==================================================

maya_path = Path(__file__).parent / "assets" / "Maya_image.jpeg"

#* New path for Haemoglobin session 

pymol_session_path = Path(__file__).parent / "assets" / "7VDE_Haemoglobin.pse"

# ==================================================
# CONNECT TO HIDDEN HEMERA FILES
# ==================================================

hidden_folder = Path(__file__).parent.parent / "hidden"
sys.path.append(str(hidden_folder))

from hemera_reference import profile_A, profile_B
from oracle_security import check_access


# * New file for retrieving hidden answers for the protein stage 
from protein_reference import (
    BETA_CHAINS,
    ALPHA_CHAINS,
    ACCEPTED_PROTEIN_NAMES,
    HBB_PROTEIN,
    HBA_PROTEIN,
    HBA_CDS,
    HBB_CDS,
    HBS_CDS,
)


# ==================================================
# >>> NEW: PRE-STAGE SETTINGS (adjust these)
# ==================================================
 
# !Set a full path here if PyMOL is not on your system PATH
# e.g. r"C:\Program Files\PyMOL\PyMOLWin.exe"

if platform.system() == "Darwin":
    PYMOL_PATH = "/Applications/PyMOL.app/Contents/MacOS/PyMOL"

elif platform.system() == "Windows":
    PYMOL_PATH = r"C:\Users\MEPI\AppData\Local\Schrodinger\PyMOL2\Menu\PyMOL + Console.bat"

else:
    PYMOL_PATH = None

MAX_PRIMER_ATTEMPTS = 4          # "four attempts maximum"
ALLOW_RETRY_AFTER_LOCKOUT = True # after 4 failures, offer a restart of page 2
 
PRIMER_LENGTH_RANGE = (18, 25)   # allowed primer length (nt)
PRIMER_GC_RANGE = (40, 60)       # allowed GC content (%)
MAX_TM_DIFFERENCE = 5.0          # max Tm gap between the two primers (deg C)
PRIMER_END_TOLERANCE = 5         # how far from the gene ends a primer may sit (nt)
PCR_CYCLES = 30                  # cycles shown in the PCR animation


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
selected_chain = None        # chain letter the player chose, e.g. "A"
selected_chain_type = None   # "alpha" or "beta"
verified_cds = None
oracle_unlocked = False
MARKER_POSITIONS = [
    10, 32, 54, 76, 98,
    120, 142, 164, 186, 208,
    231, 253, 275, 297, 319,
    341, 363, 385, 407, 430
]

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

#HOMEPAGE FUNCTION
def show_home():

    clear_screen()

    title(
        "PROFESSOR X // INVESTIGATION TERMINAL",
        "Select an investigation module"
    )

    tk.Button(
        scrollable_frame,
        text="BEGIN MOLECULAR ANALYSIS",
        command=show_protein_lookup,
        font=FONT_BOLD,
        width=30
    ).pack(
        pady=(60, 15)
    )

    oracle_button = tk.Button(
        scrollable_frame,
        text="ACCESS ORACLE",
        command=show_access,
        font=FONT_BOLD,
        width=30
    )

    oracle_button.pack(
        pady=15
    )

    if not oracle_unlocked:

        oracle_button.config(
            state="disabled"
        )

        tk.Label(
            scrollable_frame,
            text="ORACLE ACCESS LOCKED\nComplete molecular analysis first.",
            font=FONT
        ).pack(
            pady=5
        )
# ==================================================
# >>> NEW: PRE-STAGE HELPER FUNCTIONS
# ==================================================
 

def launch_pymol(session_file):
    """Open the local PyMOL session in its own window. Returns an error string or None."""
 
    if not session_file.exists():
        return (
            "PyMOL session file not found.\n"
            f"Expected file:\n{session_file}"
        )
 
    pymol_exe = PYMOL_PATH or shutil.which("pymol")
 
    if not pymol_exe:
        return (
            "PyMOL was not found.\n"
            "Install PyMOL, or set PYMOL_PATH at the top of the script."
        )
 
    try:
 
        subprocess.Popen(
            [pymol_exe, str(session_file)]
        )
 
        return None
 
    except Exception as error:
 
        return f"PyMOL could not be started:\n{error}"
 
 
def clean_protein(text):
    """Remove FASTA header lines, spaces and line breaks."""
 
    lines = [
        line for line in text.splitlines()
        if not line.strip().startswith(">")
    ]
 
    return re.sub(r"\s+", "", "".join(lines)).upper()
 
 
def clean_dna(text):
 
    return re.sub(r"[\s\-]+", "", text).upper()
 
 
def reverse_complement(seq):
 
    return seq[::-1].translate(str.maketrans("ACGT", "TGCA"))
 
 
def gc_percent(seq):
 
    return 100 * (seq.count("G") + seq.count("C")) / len(seq)
 
 
def melting_temp(seq):
 
    gc = seq.count("G") + seq.count("C")
 
    return 64.9 + 41 * (gc - 16.4) / len(seq)
 
 
def first_difference(a, b):
    """1-based position of the first residue that differs, or None."""
 
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i + 1
 
    return None
 
 
def evaluate_primers(forward, reverse):
    """Return (success, list_of_messages)."""
 
    target = verified_cds
    global primer_result
 
    problems = []
    valid = {}
 
    for label, primer in (("Forward", forward), ("Reverse", reverse)):
 
        if not primer:
            problems.append(f"{label} primer is empty.")
            continue
 
        if set(primer) - set("ACGT"):
            problems.append(f"{label} primer: use only A, C, G and T.")
            continue
 
        valid[label] = primer
 
        low, high = PRIMER_LENGTH_RANGE
 
        if not low <= len(primer) <= high:
            problems.append(
                f"{label} primer is {len(primer)} nt. "
                f"Aim for {low}-{high} nt."
            )
 
        gc_low, gc_high = PRIMER_GC_RANGE
        gc = gc_percent(primer)
 
        if not gc_low <= gc <= gc_high:
            problems.append(
                f"{label} primer GC content is {gc:.0f}%. "
                f"Aim for {gc_low}-{gc_high}%."
            )
 
    # ---------- binding checks ----------
 
    f_pos = None
    r_end = None
 
    if "Forward" in valid:
 
        f_pos = target.find(valid["Forward"])
 
        if f_pos == -1:
            problems.append(
                "Forward primer does not match the sense strand "
                "of the reference sequence."
            )
 
        elif f_pos > PRIMER_END_TOLERANCE:
            problems.append(
                "Forward primer binds too far into the gene: "
                "the start of the coding sequence would be missed."
            )
 
    if "Reverse" in valid:
 
        r_pos = target.find(reverse_complement(valid["Reverse"]))
 
        if r_pos == -1:
 
            if target.find(valid["Reverse"]) != -1:
                problems.append(
                    "Reverse primer copies the sense strand. "
                    "It must anneal to the opposite strand "
                    "(think about 5'->3' orientation)."
                )
            else:
                problems.append(
                    "Reverse primer does not bind the reference sequence."
                )
 
        else:
 
            r_end = r_pos + len(valid["Reverse"])
 
            if r_end < len(target) - PRIMER_END_TOLERANCE:
                problems.append(
                    "Reverse primer binds too far from the end of the gene: "
                    "the 3' end of the coding sequence would be missed."
                )
 
    # ---------- melting temperatures ----------
 
    if len(valid) == 2:
 
        tm_f = melting_temp(valid["Forward"])
        tm_r = melting_temp(valid["Reverse"])
 
        if abs(tm_f - tm_r) > MAX_TM_DIFFERENCE:
            problems.append(
                f"Melting temperatures differ by {abs(tm_f - tm_r):.1f} C "
                f"(Forward {tm_f:.1f} C, Reverse {tm_r:.1f} C). "
                f"Keep them within {MAX_TM_DIFFERENCE:.0f} C."
            )
 
    if problems:
        return False, problems
 
    primer_result = {
        "forward": valid["Forward"],
        "reverse": valid["Reverse"],
        "tm_f": melting_temp(valid["Forward"]),
        "tm_r": melting_temp(valid["Reverse"]),
        "amplicon": r_end - f_pos,
    }
 
    return True, []
 
 
# ==================================================
# >>> NEW: PRE-STAGE 1 — PAGE 1: PROTEIN LOOKUP
# ==================================================
 
def show_protein_lookup():
 
    clear_screen()
 
    title(
        "ORACLE // NYX",
        "A popular analysis program built by Professor X\n"
        "The ability to go from protein to DNA"
    )
 
 
    tk.Label(
        scrollable_frame,
        text=(
            "MNEMOSYNE\n"
            "Enter a name of the protein."
        ),
        font=FONT,
        justify="center"
    ).pack(
        pady=20
    )
 
 
    protein_entry = tk.Entry(
        scrollable_frame,
        width=30,
        font=("Courier New", 15),
        justify="center"
    )
 
    protein_entry.pack(
        pady=10
    )
 
 
    status = tk.Label(
        scrollable_frame,
        text="",
        font=FONT,
        justify="center"
    )
 
    status.pack(
        pady=10
    )
 
 
    # Tools that appear after a successful lookup
    tool_frame = tk.Frame(
        scrollable_frame
    )
 
    def open_pymol():
 
        error = launch_pymol(pymol_session_path)
 
        if error:
            status.config(text=error)
        else:
            status.config(
                text=(
                    "PyMOL launched in a separate window.\n"
                    "Explore the structure."
                )
            )
 
 
    def show_hint():
 
        status.config(
            text=(
                "HINT: haemoglobin has two alpha and two beta chains.\n"
                "In PyMOL, use Display > Sequence to read each chain.\n"
            )
        )
 
 
    def confirm_subunit():
 
        global selected_chain
        global selected_chain_type
    
        answer = subunit_entry.get().strip().upper()
    
        chain = answer.split()[-1] if answer else ""
    
        if chain in BETA_CHAINS:
    
            selected_chain = chain
            selected_chain_type = "beta"
    
        elif chain in ALPHA_CHAINS:
    
            selected_chain = chain
            selected_chain_type = "alpha"
    
        else:
    
            status.config(
                text=(
                    "Enter a chain letter shown in the structure.\n"
                    "Example: A"
                )
            )
    
            return
    
    
        # Same neutral message for alpha and beta, so nothing is given away
        status.config(
            text=(
                f"CHAIN {chain} SELECTED\n"
                "LOADING MOLECULAR ANALYSIS..."
            )
        )
    
        root.after(
            1500,
            show_molecular_analysis
        )
    
 
 
    def search_protein():
 
        name = protein_entry.get().strip().lower()
 
        if name not in ACCEPTED_PROTEIN_NAMES:
 
            status.config(
                text="NO MATCH FOUND IN PROTEIN DATABASE"
            )
 
            return
 
 
        if not pymol_session_path.exists():
 
            status.config(
                text=(
                    "STRUCTURE FILE NOT FOUND\n"
                    f"Expected PyMOL session:\n{pymol_session_path}"
                )
            )
 
            return
 
 
        status.config(
            text=(
                "MATCH FOUND: HAEMOGLOBIN\n"
                "3D structure retrieved.\n"
                "Launch PyMOL to explore it."
            )
        )
 
        search_button.config(state="disabled")
        protein_entry.config(state="disabled")
 
        tool_frame.pack(
            pady=15
        )
 
 
    search_button = tk.Button(
        scrollable_frame,
        text="SEARCH PROTEIN DATABASE",
        command=search_protein,
        font=FONT_BOLD,
        width=28
    )
 
    search_button.pack(
        pady=10
    )
 
 
    # ---------- widgets inside tool_frame ----------
 
    tk.Button(
        tool_frame,
        text="LAUNCH PYMOL",
        command=open_pymol,
        font=FONT_BOLD,
        width=28
    ).pack(
        pady=(10, 20)
    )
 
 
    tk.Label(
        tool_frame,
        text="Which subunit would you like to analyse? \n(enter the PyMol chain letter)",
        font=FONT_BOLD,
        justify="center"
    ).pack(
        pady=5
    )
 
 
    subunit_entry = tk.Entry(
        tool_frame,
        width=10,
        font=("Courier New", 15),
        justify="center"
    )
 
    subunit_entry.pack(
        pady=10
    )
 
 
    tk.Button(
        tool_frame,
        text="CONFIRM SUBUNIT",
        command=confirm_subunit,
        font=FONT_BOLD,
        width=28
    ).pack(
        pady=5
    )
 
 
    tk.Button(
        tool_frame,
        text="SHOW HINT",
        command=show_hint,
        font=FONT,
        width=28
    ).pack(
        pady=(5, 30)
    )
 
 
# ==================================================
# >>> NEW: PRE-STAGE 1 — PAGE 2: MOLECULAR ANALYSIS
# ==================================================



def show_molecular_analysis():
 
    global primer_attempts
 
    primer_attempts = 0
 
    clear_screen()
 
    title(
        "MOLECULAR ANALYSIS",
        f"PRE-STAGE 1 - PAGE 2: CHAIN {selected_chain}"
    )
 
    # ==========================
    # TOOL 1 — REVERSE PROTEIN SEQUENCE
    # ==========================
 
    tool1_frame = tk.LabelFrame(
        scrollable_frame,
        text= (
        "ORACLE will trace the gene behind the selected subunit. \n Tool 1 retrieves the gene's coding DNA from the protein." 
        "\n Tool 2 designs the primers needed to amplify it."),
        font=FONT_BOLD,
        padx=20,
        pady=15
    )
 
    tool1_frame.pack(
        fill="x",
        padx=70,
        pady=15
    )
 
 
    tk.Label(
        tool1_frame,
        text=(
            f"Submit the complete amino-acid sequence of chain {selected_chain}\n"
            "(one-letter code)."
        ),
        font=FONT,
        justify="left"
    ).pack(
        anchor="w"
    )


 
    global sequence_box, status1, cds_label, cds_box, verify_button
    global forward_entry, reverse_entry, primer_button, attempts_label, status2

    sequence_box = tk.Text(
        tool1_frame,
        width=80,
        height=5,
        font=("Courier New", 10),
        wrap="char"
    )
 
    sequence_box.pack(
        pady=10
    )
 
 
    status1 = tk.Label(
        tool1_frame,
        text="",
        font=FONT,
        justify="left"
    )
    status1.pack(anchor="w", pady=(0, 10))
 
    verify_button = tk.Button(
        tool1_frame,
        text="VERIFY SEQUENCE",
        command=verify_sequence,
        font=FONT_BOLD,
        width=24
    )
    verify_button.pack(pady=5)

    tk.Button(
        tool1_frame,
        text="SHOW HINT",
        command=show_hint_pymol,
        font=FONT,
        width=28
    ).pack(
        pady=(5, 30)
    )
 
    cds_label = tk.Label(
        tool1_frame,
        text="REFERENCE DNA CODING SEQUENCE:",
        font=FONT_BOLD
    )
 
    cds_box = tk.Text(
        tool1_frame,
        width=80,
        height=7,
        font=("Courier New", 10),
        wrap="char"
    )
    cds_box.config(state="disabled")

        # ==========================
    # TOOL 2 — PRIMER DESIGN
    # ==========================
 
    tool2_frame = tk.LabelFrame(
        scrollable_frame,
        text="TOOL 2 - PRIMER DESIGN (LOCKED UNTIL TOOL 1 IS VERIFIED)",
        font=FONT_BOLD,
        padx=20,
        pady=15
    )
 
    tool2_frame.pack(
        fill="x",
        padx=70,
        pady=15
    )
 
 
    tk.Label(
        tool2_frame,
        text=(
            "Design a forward and a reverse primer (5'->3') that amplify\n"
            "the whole coding sequence."
        ),
        font=FONT,
        justify="left"
    ).pack(
        anchor="w",
        pady=(0, 10)
    )
 
 
    tk.Label(
        tool2_frame,
        text="FORWARD PRIMER 5'->3':",
        font=FONT_BOLD
    ).pack(
        anchor="w"
    )
 
    forward_entry = tk.Entry(
        tool2_frame,
        width=40,
        font=("Courier New", 12),
        state="disabled"
    )
 
    forward_entry.pack(
        anchor="w",
        pady=(2, 10)
    )
 
 
    tk.Label(
        tool2_frame,
        text="REVERSE PRIMER 5'->3':",
        font=FONT_BOLD
    ).pack(
        anchor="w"
    )
 
    reverse_entry = tk.Entry(
        tool2_frame,
        width=40,
        font=("Courier New", 12),
        state="disabled"
    )
 
    reverse_entry.pack(
        anchor="w",
        pady=(2, 10)
    )
 
 
    attempts_label = tk.Label(
        tool2_frame,
        text=f"Attempts remaining: {MAX_PRIMER_ATTEMPTS}",
        font=FONT
    )
 
    attempts_label.pack(
        anchor="w",
        pady=5
    )
 
 
    status2 = tk.Label(
        tool2_frame,
        text="",
        font=FONT,
        justify="left"
    )
 
 
    def submit_primers():
 
        global primer_attempts
 
        forward = clean_dna(forward_entry.get())
        reverse = clean_dna(reverse_entry.get())
 
        primer_attempts += 1
 
        success, problems = evaluate_primers(forward, reverse)
 
        remaining = MAX_PRIMER_ATTEMPTS - primer_attempts
 
        attempts_label.config(
            text=f"Attempts remaining: {max(remaining, 0)}"
        )
 
 
        if success:
 
            status2.config(
                text="PRIMERS ACCEPTED"
            )
 
            primer_button.config(state="disabled")
            forward_entry.config(state="disabled")
            reverse_entry.config(state="disabled")
 
            root.after(
                1200,
                show_pcr_success
            )
 
            return
 
 
        message = "PRIMER CHECK FAILED\n\n" + "\n".join(
            f"- {problem}" for problem in problems
        )
 
 
        if remaining <= 0:
 
            message += "\n\nNO ATTEMPTS REMAINING. PRIMER DESIGN LOCKED."
 
            primer_button.config(state="disabled")
            forward_entry.config(state="disabled")
            reverse_entry.config(state="disabled")
 
            if ALLOW_RETRY_AFTER_LOCKOUT:
 
                tk.Button(
                    tool2_frame,
                    text="REBOOT MOLECULAR ANALYSIS",
                    command=show_molecular_analysis,
                    font=FONT_BOLD,
                    width=28
                ).pack(
                    pady=10
                )
 
        status2.config(text=message)
 
        scroll_to_bottom()
 
 
    primer_button = tk.Button(
        tool2_frame,
        text="SUBMIT PRIMERS",
        command=submit_primers,
        font=FONT_BOLD,
        width=24,
        state="disabled"
    )
 
    primer_button.pack(
        pady=5
    )
 
    status2.pack(
        pady=5,
        anchor="w"
    )

def show_hint_pymol():

    status1.config(
        text=(
            "HINT: Use print(cmd.get_fastastr('all')) to acquire protein sequence"
        )
    )


def verify_sequence():
 
    global verified_cds
    submitted = clean_protein(sequence_box.get("1.0", "end"))
 
    if not submitted:
        status1.config(text="Paste or type a sequence first.")
        return
 
 
    # The gene to expect depends on the chain chosen on page 1
    if selected_chain_type == "alpha":
 
        expected_protein = HBA_PROTEIN
        expected_cds = HBA_CDS
        gene_label = "HBA alpha-globin"
        other_protein = HBB_PROTEIN
 
    else:
 
        expected_protein = HBB_PROTEIN
        expected_cds = HBB_CDS
        gene_label = "HBB beta-globin"
        other_protein = HBA_PROTEIN
 
 
    # ---------- correct sequence ----------
 
    if submitted == expected_protein:
 
        verified_cds = expected_cds
 
        status1.config(
            text=(
                f"SEQUENCE VERIFIED: {gene_label} "
                f"({len(expected_protein)} aa)\n"
                "Reference coding sequence retrieved."
            )
        )
 
        cds_label.pack(anchor="w", pady=(10, 2))
 
        cds_box.pack(pady=5)
 
        cds_box.config(state="normal")
        cds_box.delete("1.0", "end")
        cds_box.insert("1.0", expected_cds)
        cds_box.config(state="disabled")
 
        verify_button.config(state="disabled")
        sequence_box.config(state="disabled")
 
        # unlock Tool 2
        forward_entry.config(state="normal")
        reverse_entry.config(state="normal")
        primer_button.config(state="normal")
 
        scroll_to_bottom()
 
        return
 
 
    # ---------- not amino-acid letters ----------
 
    if set(submitted) - set("ACDEFGHIKLMNPQRSTVWY"):
 
        status1.config(
            text=(
                "SEQUENCE ERROR:\n"
                "Use only the 20 amino-acid one-letter codes."
            )
        )
 
        return
 
 
    # ---------- sequence of the other subunit ----------
 
    if submitted in (other_protein, other_protein[1:]):
 
        status1.config(
            text=(
                "SEQUENCE MISMATCH\n"
                f"This belongs to a different subunit from chain "
                f"{selected_chain}."
            )
        )
 
        return
 
 
    # ---------- mature chain without the initiator methionine ----------
 
    if submitted == expected_protein[1:]:
 
        status1.config(
            text=(
                f"Close! This is the mature {len(expected_protein) - 1}-aa "
                "chain seen in the 3D model.\n"
                "The gene is translated starting from the initiator\n"
                "methionine, which is later removed. Submit the\n"
                f"complete {len(expected_protein)}-aa sequence."
            )
        )
 
        return
 
 
    # ---------- anything else ----------
 
    position = first_difference(submitted, expected_protein)
 
    status1.config(
        text=(
            "SEQUENCE MISMATCH\n"
            f"Submitted length: {len(submitted)} aa\n"
            + (
                f"First difference at residue {position}."
                if position
                else "Sequence is incomplete or has extra residues."
            )
        )
    )
 
 

 

 
# ==================================================
# >>> NEW: PCR SUCCESS
# ==================================================
 
def show_pcr_success():
 
    clear_screen()
 
    title(
        "PCR SUCCESS"
    )
 
 
    cycle_label = tk.Label(
        scrollable_frame,
        text="Running thermal cycler...",
        font=("Courier New", 14),
        justify="center"
    )
 
    cycle_label.pack(
        pady=(40, 20)
    )
 
 
    result_label = tk.Label(
        scrollable_frame,
        text="",
        font=FONT,
        justify="center"
    )
 
    result_label.pack(
        pady=10
    )
 
 
    def tick(cycle):
 
        if cycle <= PCR_CYCLES:
 
            cycle_label.config(
                text=(
                    f"Cycle {cycle}/{PCR_CYCLES}\n"
                    f"Template copies: 2^{cycle}"
                )
            )
 
            root.after(
                100,
                tick,
                cycle + 1
            )
 
            return
 
 
        cycle_label.config(
            text="Amplification complete."
        )
 
        result_label.config(
            text=(
                "Correct primers accepted.\n"
                "DNA amplification confirmed in the\n"
                "PCR .\n\n"
                f"Forward primer: {primer_result['forward']}"
                f"  (Tm {primer_result['tm_f']:.1f} C)\n"
                f"Reverse primer: {primer_result['reverse']}"
                f"  (Tm {primer_result['tm_r']:.1f} C)\n"
                f"Amplicon size: {primer_result['amplicon']}bp\n"
                f"Keep a record of the sample's sequence"
            )
        )

        tk.Label(scrollable_frame, text="SAMPLE cDNA SEQUENCE:", font=FONT_BOLD).pack(pady=(10, 2))

        cds_display = tk.Text(scrollable_frame, width=80, height=7, font=("Courier New", 10), wrap="char")
        if verified_cds == HBA_CDS:
            cds_display.insert("1.0", HBA_CDS)
        else:
            cds_display.insert("1.0", HBS_CDS)
        cds_display.config(state="disabled")
        cds_display.pack(pady=5)

        global oracle_unlocked
        oracle_unlocked = True
        tk.Button(
            scrollable_frame,
            text="RETURN TO MAIN TERMINAL",
            command=show_home,
            font=FONT_BOLD,
            width=28
        ).pack(
            pady=30
        )
 
 
    root.after(
        500,
        tick,
        1
    )

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
                "Use NYX to recover the genetic information from the\n"
                "biological trace found in Professor X's laboratory.\n\n"
                "Paste the complete DNA sequence recovered from the previous analysis."
            ),
            font=FONT,
            justify="center"
        ).pack(
            pady=20
        )

        tk.Label(
            scrollable_frame,
            text="Paste the complete DNA sequence below:",
            font=FONT_BOLD
        ).pack(
            pady=10
        )

        profile_entry = tk.Entry(
            scrollable_frame,
            width=95,
            font=("Courier New", 12),
            justify="left"
        )

        profile_entry.pack(
            pady=10,
            padx=20
        )

        tk.Label(
            scrollable_frame,
            text=(
                "Paste the complete nucleotide sequence.\n"
                "ORACLE will automatically extract the predefined\n"
                "identification markers required for comparison."
            ),
            font=("Courier New", 10),
            justify="center"
        ).pack(
            pady=5
        )

        status = tk.Label(
            scrollable_frame,
            text="",
            font=FONT,
            justify="center"
        )

        status.pack(
            pady=10
        )

        def submit_profile():

            global crime_sample

            # Read the full sequence typed/pasted by the player
            full_sequence = clean_dna(
                profile_entry.get()
            )

            # Nothing entered
            if not full_sequence:

                status.config(
                    text=(
                        "ERROR:\n"
                        "Paste the DNA sequence first."
                    )
                )

                return

            # Make sure sequence contains only DNA bases
            if set(full_sequence) - set("ACGT"):

                status.config(
                    text=(
                        "ERROR:\n"
                        "The sequence must contain only A, C, G and T."
                    )
                )

                return

            # Make sure the sequence is long enough
            # because the largest marker index is 430
            if len(full_sequence) <= max(MARKER_POSITIONS):

                status.config(
                    text=(
                        "ERROR:\n"
                        "The submitted DNA sequence is incomplete.\n"
                        f"Sequence length detected: {len(full_sequence)} nucleotides."
                    )
                )

                return

            # Extract the 20 selected marker positions
            crime_sample = [
                full_sequence[i]
                for i in MARKER_POSITIONS
            ]

            status.config(
                text=(
                    "SEQUENCE ACCEPTED\n"
                    "20 identification markers extracted."
                )
            )

            root.after(
                1000,
                show_code_challenge
            )


        # IMPORTANT:
        # command=submit_profile
        # NOT command=submit_profile()
        tk.Button(
            scrollable_frame,
            text="LOAD SEQUENCE",
            command=submit_profile,
            font=FONT_BOLD,
            width=20
        ).pack(
            pady=15
        )
        tk.Button(
            scrollable_frame,
            text="RETURN TO MAIN TERMINAL",
            command=show_home,
            font=FONT_BOLD,
            width=28
        ).pack(
            pady=30
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


show_home()
#show_access()

root.mainloop()