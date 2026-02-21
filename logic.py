import json
from fpdf import FPDF
import datetime

DB_FILE = "database.json"

# --- HELPERS ---
def load_data():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_parameter_names():
    data = load_data()
    return sorted([item["name"] for item in data])

def sanitize(text):
    """Protects PDF from crashing on special characters"""
    if isinstance(text, (int, float)):
        return str(text)
    return text.encode('latin-1', 'ignore').decode('latin-1')

# --- PART A: BATCH ANALYSIS ---
def analyze_batch(batch_data):
    db = load_data()
    gui_text = []
    pdf_results = []
    
    # GUI Header
    gui_text.append(("HEADER", f"COMPREHENSIVE ANALYSIS REPORT"))
    gui_text.append(("NORMAL", f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"))
    gui_text.append(("NORMAL", "="*60 + "\n"))

    for item in batch_data:
        p_name = item['name']
        val = item['value']
        
        param_obj = next((x for x in db if x["name"] == p_name), None)
        if not param_obj: continue

        gui_text.append(("SUBHEADER", f"► {p_name} (Result: {val} {param_obj['unit']})"))
        
        pdf_entry = {
            "parameter": p_name,
            "value": f"{val} {param_obj['unit']}",
            "standards": []
        }

        for std in param_obj['standards']:
            authority = std['authority']
            limit_max = std.get('max_limit')
            limit_min = std.get('min_limit')
            
            is_unsafe = False
            violation_txt = ""

            if limit_max is not None and val > limit_max:
                is_unsafe = True
                violation_txt = f"> {limit_max}"
            if limit_min is not None and val < limit_min:
                is_unsafe = True
                violation_txt = f"< {limit_min}"
            
            std_entry = {
                "authority": authority,
                "status": "PASS",
                "limit": f"{limit_min}-{limit_max}" if limit_min else f"Max {limit_max}",
                "color": (0, 150, 0),    # GREEN
                "symbol": "3"            # Checkmark
            }

            if is_unsafe:
                std_entry.update({
                    "status": "FAIL",
                    "color": (200, 0, 0), # RED
                    "violation": violation_txt,
                    "consequence": std['consequence'],
                    "solution": std['solution'],
                    "symbol": "7"         # X-Mark
                })
                gui_text.append(("FAIL", f"   ❌ [{authority}] FAIL: {violation_txt}"))
                gui_text.append(("NORMAL", f"      Consequence: {std['consequence']}"))
                gui_text.append(("NORMAL", f"      Solution: {std['solution']}"))
            
            elif limit_max is None and limit_min is None:
                std_entry.update({"status": "INFO", "color": (0, 0, 200), "symbol": "s"}) 
                gui_text.append(("INFO", f"   ℹ️ [{authority}] INFO: No Limit"))
            
            else:
                gui_text.append(("PASS", f"   ✅ [{authority}] PASS"))
            
            pdf_entry["standards"].append(std_entry)

        pdf_results.append(pdf_entry)
        gui_text.append(("NORMAL", "-"*40 + "\n"))

    return gui_text, pdf_results

def save_comprehensive_pdf(results):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Comprehensive Water Quality Report", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # SUMMARY TABLE
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. SUMMARY OF RESULTS", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    
    pdf.cell(60, 8, "Parameter", 1, 0, 'L', 1)
    pdf.cell(40, 8, "Value", 1, 0, 'C', 1)
    pdf.cell(90, 8, "Status", 1, 1, 'L', 1)
    
    pdf.set_font("Arial", '', 10)
    for res in results:
        overall_status = "SAFE"
        for s in res['standards']:
            if s['status'] == "FAIL": overall_status = "UNSAFE"
            
        pdf.cell(60, 8, sanitize(res['parameter']), 1)
        pdf.cell(40, 8, sanitize(res['value']), 1, 0, 'C')
        
        if overall_status == "UNSAFE":
            pdf.set_text_color(200, 0, 0)
            pdf.cell(90, 8, "FLAGGED ISSUES", 1, 1)
        else:
            pdf.set_text_color(0, 150, 0)
            pdf.cell(90, 8, "PASSED", 1, 1)
        pdf.set_text_color(0, 0, 0)

    pdf.ln(10)

    # DETAILED BREAKDOWN
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DETAILED ANALYSIS & SOLUTIONS", ln=True)
    
    for res in results:
        pdf.set_text_color(200, 150, 0)
        pdf.set_font("ZapfDingbats", '', 10)
        pdf.cell(8, 8, 'z', 0, 0)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, f"{sanitize(res['parameter'])} (Result: {sanitize(res['value'])})", ln=True)
        pdf.set_text_color(0, 0, 0)

        for std in res['standards']:
            pdf.set_text_color(*std['color'])
            pdf.set_font("ZapfDingbats", '', 10)
            pdf.cell(10, 6, std['symbol'], 0, 0) 
            
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 6, f" {sanitize(std['authority'])} (Limit: {sanitize(std['limit'])})", ln=True)
            
            pdf.set_text_color(50, 50, 50)
            if "consequence" in std:
                clean_cons = sanitize(std['consequence'])
                clean_sol = sanitize(std['solution'])
                pdf.multi_cell(0, 5, f"      Risk: {clean_cons}")
                pdf.multi_cell(0, 5, f"      Fix: {clean_sol}")
                pdf.ln(2)
        pdf.ln(3)

    filename = f"Analysis_Report_{datetime.datetime.now().strftime('%M%S')}.pdf"
    pdf.output(filename)
    return filename

# --- PART B: PROPOSAL (UPDATED) ---
def generate_proposal(inputs):
    # 1. SETUP VARIABLES
    p_current = inputs['pop_current']
    rate = inputs['growth_rate']
    years = inputs['design_period']
    
    calc_steps = []
    
    # 2. POPULATION CALCULATIONS (With Steps)
    if inputs['type'] == "City (Geometric)":
        method = "Geometric Progression Method"
        calc_steps.append("FORMULA: Pn = Po * (1 + r/100)^n")
        calc_steps.append(f"SUBSTITUTION: {p_current} * (1 + {rate}/100)^{years}")
        
        factor = (1 + rate/100) ** years
        p_future = int(p_current * factor)
        
        calc_steps.append(f"GROWTH FACTOR: {factor:.4f}")
        calc_steps.append(f"RESULT: {p_future:,} people")
        per_capita = 120
        
    else: # Village (Arithmetic)
        method = "Arithmetic Progression Method"
        calc_steps.append("FORMULA: Pn = Po + (n * Increase_per_year)")
        calc_steps.append("STEP 1: Calculate Annual Increase = (Rate/100) * Po")
        
        yearly_increase = int((rate/100) * p_current)
        calc_steps.append(f"        Increase = ({rate}/100) * {p_current} = {yearly_increase} people/year")
        
        calc_steps.append(f"STEP 2: Add growth over {years} years")
        calc_steps.append(f"        {p_current} + ({years} * {yearly_increase})")
        
        p_future = int(p_current + (years * yearly_increase))
        calc_steps.append(f"RESULT: {p_future:,} people")
        per_capita = 60

    # 3. DEMAND CALCULATIONS (With Steps)
    demand_steps = []
    avg_daily_demand = p_future * per_capita
    max_daily_demand = avg_daily_demand * 1.15
    
    demand_steps.append(f"Assumed Per Capita Demand: {per_capita} Liters/person/day (based on community type)")
    demand_steps.append(f"AVG DAILY DEMAND (Q_avg) = Population * Per Capita")
    demand_steps.append(f"                       = {p_future:,} * {per_capita}")
    demand_steps.append(f"                       = {avg_daily_demand:,.0f} Liters/day")
    
    demand_steps.append(f"MAX DAILY DEMAND (Q_max) = Q_avg * Peak Factor (1.15)")
    demand_steps.append(f"                       = {avg_daily_demand:,.0f} * 1.15")
    demand_steps.append(f"                       = {max_daily_demand:,.0f} Liters/day")

    # 4. EXPANDED TREATMENT LOGIC
    source_details = ""
    treatment_steps = []
    
    if "River" in inputs['source']:
        source_details = "Raw water source: Surface water (River/Stream). High risk of turbidity, suspended solids, and bacteriological contamination."
        treatment_steps = [
            ("1. Intake & Screening", "Water abstraction via intake tower. Coarse bar screens (20mm) remove floating debris like leaves, branches, and plastics."),
            ("2. Aeration (Cascade)", "Water flows down steps to trap oxygen. Removes taste/odor gases and oxidizes dissolved Iron/Manganese."),
            ("3. Coagulation (Flash Mix)", "Rapid mixing of Alum (Aluminum Sulfate) to neutralize charges of fine particles."),
            ("4. Flocculation", "Slow mixing in flocculator basins allows particles to collide and form heavy 'floc'."),
            ("5. Sedimentation", "Water enters clarifying tanks. Heavy floc settles to the bottom as sludge (Detention time: 2-4 hours)."),
            ("6. Filtration", "Rapid Sand Filters remove remaining suspended solids and 90% of bacteria."),
            ("7. Disinfection", "Chlorine dosing (contact time 30 mins) to kill remaining pathogens and prevent re-contamination in pipes."),
            ("8. Storage", "Clear water reservoir stores treated water for distribution.")
        ]
    elif "Borehole" in inputs['source']:
        source_details = "Raw water source: Deep Groundwater. Generally low turbidity but potential for dissolved Iron, Manganese, Hardness, or Fluoride."
        treatment_steps = [
            ("1. Aeration", "Essential step. Sprays water into air to precipitate dissolved Iron (red water) and remove 'Rotten Egg' smell (H2S)."),
            ("2. pH Correction", "If water is acidic (pH < 6.5), Lime is dosed to prevent pipe corrosion."),
            ("3. Softening (Optional)", "If Hardness > 150mg/L, an Ion Exchange unit or Lime-Soda process reduces calcium/magnesium levels."),
            ("4. Filtration (Pressure Sand)", "Removes the Iron precipitates formed during the aeration step."),
            ("5. Disinfection", "Protective Chlorination to maintain residual safety in the distribution network."),
            ("6. Elevated Storage", " pumped to overhead tank for gravity distribution.")
        ]
    else: # Rainwater
        source_details = "Raw water source: Rainwater Harvesting. Generally pure but risk of roof contamination (bird droppings, dust, leaves)."
        treatment_steps = [
            ("1. Catchment & Gutters", "Collection from roof surfaces using PVC gutters."),
            ("2. First Flush Diverter", "CRITICAL: A device that discards the first 10-20 Liters of rain which carries the most dirt/dust from the roof."),
            ("3. Screening", "Wire mesh filters at downpipe entry to stop leaves and insects."),
            ("4. Sedimentation Tank", "Allows fine dust to settle before water enters main storage."),
            ("5. Filtration", "Slow Sand Filter or Charcoal filter to improve taste and remove color."),
            ("6. Disinfection", "Chlorination or UV Sterilization is required before drinking.")
        ]

    # --- PDF GENERATION ---
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 20, "PROJECT PROPOSAL", ln=True, align='C')
    pdf.set_font("Arial", '', 16)
    pdf.cell(0, 10, "WATER SUPPLY SCHEME DESIGN", ln=True, align='C')
    pdf.ln(10)
    
    # Metadata
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"PROJECT: {sanitize(inputs['name'])}", ln=True)
    pdf.cell(0, 8, f"SOURCE: {sanitize(inputs['source'])}", ln=True)
    pdf.cell(0, 8, f"DATE: {datetime.date.today()}", ln=True)
    pdf.ln(5)
    
    # 1. POPULATION WORKINGS
    pdf.set_fill_color(220, 230, 241) # Light Blue
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1.0 POPULATION PROJECTION", 1, 1, 'L', 1)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, f"Method: {method}", ln=True)
    
    pdf.set_font("Courier", '', 10) # Monospace for math alignment
    for line in calc_steps:
        pdf.cell(0, 6, sanitize(line), ln=True)
    pdf.ln(5)

    # 2. DEMAND WORKINGS
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2.0 WATER DEMAND CALCULATIONS", 1, 1, 'L', 1)
    
    pdf.set_font("Courier", '', 10)
    for line in demand_steps:
        pdf.cell(0, 6, sanitize(line), ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.ln(3)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, f" >> FINAL DESIGN CAPACITY: {max_daily_demand:,.0f} Liters/Day", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # 3. DETAILED TREATMENT
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3.0 PROPOSED TREATMENT SYSTEM", 1, 1, 'L', 1)
    
    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 6, source_details)
    pdf.ln(5)
    
    for title, desc in treatment_steps:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, title, ln=True)
        
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(3)
    
    filename = f"Proposal_{inputs['name'].replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename