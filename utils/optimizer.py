"""
Optimizer Module - Cutting Optimization Logic
โมดูลสำหรับคำนวณการตัดเหล็กอย่างมีประสิทธิภาพ (Fixed Negative Waste)
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

# Standard steel weight per meter (kg/m) by diameter (mm)
WEIGHT_MAP = {
    6: 0.222,
    9: 0.499,
    10: 0.617,
    12: 0.888,
    16: 1.578,
    20: 2.466,
    25: 3.853,
    28: 4.83,
    32: 6.31
}

@dataclass
class CuttingItem:
    """Individual cutting requirement"""
    bar_mark: str
    diameter: int
    length: float
    quantity: int

@dataclass
class StockBar:
    """Individual stock bar with cuts"""
    stock_id: int
    diameter: int
    stock_length: float
    cuts: List[Dict[str, Any]] = field(default_factory=list)
    remaining: float = 0.0
    utilization: float = 0.0
    
    # Helper for tracking cut position
    current_position: float = 0.0

@dataclass
class OptimizationResult:
    """Complete optimization result"""
    procurement_summary: List[Dict[str, Any]]
    cutting_plan: List[StockBar]
    total_waste: float
    total_stock_used: int
    remnant_summary: Dict[str, List[Dict[str, Any]]]
    total_weight: float

def apply_engineering_splicing(
    cutting_data: List[Dict[str, Any]], 
    stock_length: float,
    lap_factor: int = 40
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply engineering splicing to bars exceeding stock length
    """
    processed_data = []
    splicing_info = {
        'total_spliced': 0,
        'original_count': len(cutting_data),
        'additional_pieces': 0
    }
    
    for item in cutting_data:
        bar_mark = item['bar_mark']
        diameter = item['diameter']
        length = float(item['cut_length'])
        quantity = int(item['quantity'])
        
        if length <= stock_length:
            processed_data.append(item.copy())
        else:
            splicing_info['total_spliced'] += quantity
            lap_length = (lap_factor * diameter) / 1000.0
            
            pieces = []
            remaining_length = length
            
            # Splitting Logic
            first_piece = True
            while remaining_length > 0:
                if first_piece:
                    cut_len = stock_length
                    effective_len = stock_length
                    first_piece = False
                else:
                    if remaining_length + lap_length <= stock_length:
                        cut_len = remaining_length + lap_length
                        effective_len = remaining_length
                    else:
                        cut_len = stock_length
                        effective_len = stock_length - lap_length

                pieces.append({
                    'cut': cut_len,
                    'effective': effective_len
                })
                remaining_length -= effective_len
            
            total_pieces = len(pieces)
            splicing_info['additional_pieces'] += (total_pieces - 1) * quantity
            
            for idx, piece in enumerate(pieces, 1):
                note_text = f"Spliced from {bar_mark}"
                if idx > 1:
                    note_text += f" (Lap: {lap_length:.3f}m)"
                    
                processed_data.append({
                    'bar_mark': f"{bar_mark} ({idx}/{total_pieces})",
                    'diameter': diameter,
                    'cut_length': piece['cut'],
                    'quantity': quantity,
                    'note': note_text
                })

    splicing_info['final_count'] = len(processed_data)
    return processed_data, splicing_info

def optimize_cutting(
    cutting_data: List[Dict[str, Any]], 
    stock_length: float, 
    cutting_tolerance_mm: int
) -> OptimizationResult:
    """
    Optimize bar cutting using First Fit Decreasing algorithm
    (Fixed: Handles oversized bars to prevent negative waste)
    """
    cutting_tolerance = cutting_tolerance_mm / 1000.0
    
    # 1. Group by diameter
    diameter_groups = {}
    for item in cutting_data:
        dia = item['diameter']
        if dia not in diameter_groups:
            diameter_groups[dia] = []
        
        qty = int(item['quantity'])
        for _ in range(qty):
            diameter_groups[dia].append({
                'bar_mark': item['bar_mark'],
                'length': float(item['cut_length'])
            })

    all_cutting_plans = []
    procurement_summary = []
    total_waste_all = 0
    total_stock_used_all = 0
    total_weight_all = 0

    # 2. Process each diameter
    for diameter, items in diameter_groups.items():
        # Sort Longest to Shortest
        sorted_items = sorted(items, key=lambda x: x['length'], reverse=True)
        
        stock_bars = []
        stock_counter = 1
        
        # Separate Standard vs Oversized items (to prevent negative waste)
        standard_items = []
        oversized_items = []
        
        for item in sorted_items:
            if item['length'] <= stock_length:
                standard_items.append(item)
            else:
                oversized_items.append(item)
        
        # 2.1 Optimization for Standard Items (Fit in Stock Length)
        for item in standard_items:
            item_len = item['length']
            placed = False
            
            for stock in stock_bars:
                space_needed = item_len
                if stock.cuts:
                    space_needed += cutting_tolerance
                
                if stock.remaining >= space_needed:
                    start_pos = stock.current_position
                    if stock.cuts:
                        start_pos += cutting_tolerance
                    end_pos = start_pos + item_len
                    
                    stock.cuts.append({
                        'bar_mark': item['bar_mark'],
                        'length': item_len,
                        'start': start_pos,
                        'end': end_pos
                    })
                    
                    stock.current_position = end_pos
                    stock.remaining -= space_needed
                    stock.utilization = ((stock.stock_length - stock.remaining) / stock.stock_length) * 100
                    placed = True
                    break
            
            if not placed:
                new_stock = StockBar(
                    stock_id=stock_counter,
                    diameter=diameter,
                    stock_length=stock_length,
                    cuts=[{
                        'bar_mark': item['bar_mark'],
                        'length': item_len,
                        'start': 0.0,
                        'end': item_len
                    }],
                    remaining=stock_length - item_len,
                    utilization=(item_len / stock_length) * 100,
                    current_position=item_len
                )
                stock_bars.append(new_stock)
                stock_counter += 1
        
        # 2.2 Handle Oversized Items (Treat as Special Length)
        # กรณีนี้จะเกิดขึ้นเมื่อ User ปิด Auto-Splicing แต่มีเหล็กยาว
        for item in oversized_items:
            # ใช้ความยาวเท่ากับตัวมันเอง (Special Order) เพื่อไม่ให้ Waste ติดลบ
            actual_len = item['length']
            new_stock = StockBar(
                stock_id=stock_counter,
                diameter=diameter,
                stock_length=actual_len,
                cuts=[{
                    'bar_mark': item['bar_mark'],
                    'length': actual_len,
                    'start': 0.0,
                    'end': actual_len
                }],
                remaining=0.0, # No waste for special order
                utilization=100.0,
                current_position=actual_len
            )
            stock_bars.append(new_stock)
            stock_counter += 1

        # 3. Calculate Summary (Correctly using sum of actual stock lengths)
        total_bars_dia = len(stock_bars)
        waste_dia = sum(s.remaining for s in stock_bars)
        
        # สำคัญ: คำนวณความยาวรวมจาก Stock จริงแต่ละเส้น (รองรับกรณี Oversized)
        total_len_dia = sum(s.stock_length for s in stock_bars)
        
        waste_pct_dia = (waste_dia / total_len_dia * 100) if total_len_dia > 0 else 0
        
        unit_weight = WEIGHT_MAP.get(diameter, 0)
        weight_dia = total_len_dia * unit_weight
        
        procurement_summary.append({
            'diameter': diameter,
            'stock_length': stock_length if not oversized_items else "Mixed", # Indicate mixed if oversized exists
            'quantity': total_bars_dia,
            'total_length': total_len_dia,
            'waste': waste_dia,
            'waste_percentage': waste_pct_dia,
            'total_weight': weight_dia
        })
        
        all_cutting_plans.extend(stock_bars)
        total_waste_all += waste_dia
        total_stock_used_all += total_bars_dia
        total_weight_all += weight_dia

    # 4. Remnant Classification
    reusable = []
    scrap = []
    
    for stock in all_cutting_plans:
        if stock.remaining > 0:
            unit_w = WEIGHT_MAP.get(stock.diameter, 0)
            rem_info = {
                'stock_id': stock.stock_id,
                'diameter': stock.diameter,
                'length': stock.remaining,
                'weight': stock.remaining * unit_w
            }
            if stock.remaining >= 1.0:
                reusable.append(rem_info)
            else:
                scrap.append(rem_info)

    return OptimizationResult(
        procurement_summary=procurement_summary,
        cutting_plan=all_cutting_plans,
        total_waste=total_waste_all,
        total_stock_used=total_stock_used_all,
        remnant_summary={'reusable': reusable, 'scrap': scrap},
        total_weight=total_weight_all
    )