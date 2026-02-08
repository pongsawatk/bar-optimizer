"""
Optimizer Module - Cutting Optimization Logic
โมดูลสำหรับคำนวณการตัดเหล็กอย่างมีประสิทธิภาพ
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# Standard steel weight per meter (kg/m) by diameter (mm)
WEIGHT_MAP = {
    9: 0.499,
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
    cuts: List[Dict[str, Any]]
    remaining: float
    utilization: float


@dataclass
class OptimizationResult:
    """Complete optimization result"""
    procurement_summary: List[Dict[str, Any]]
    cutting_plan: List[StockBar]
    total_waste: float
    total_stock_used: int
    remnant_summary: Dict[str, List[Dict[str, Any]]]  # Reusable and Scrap
    total_weight: float


def apply_engineering_splicing(
    cutting_data: List[Dict[str, Any]], 
    stock_length: float,
    lap_factor: int = 40
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply engineering splicing to bars exceeding stock length
    
    Args:
        cutting_data: Original cutting requirements
        stock_length: Standard stock length in meters
        lap_factor: Lap length factor (times diameter), default 40d
        
    Returns:
        Tuple of (processed_data, splicing_info)
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
        length = item['cut_length']
        quantity = item['quantity']
        
        # Check if bar exceeds stock length
        if length <= stock_length:
            # No splicing needed
            processed_data.append(item.copy())
        else:
            # Splicing required
            splicing_info['total_spliced'] += quantity
            
            # Calculate lap length in meters
            lap_length = (lap_factor * diameter) / 1000.0
            
            # Calculate number of pieces needed
            pieces = []
            remaining_length = length
            piece_count = 1
            
            # First piece
            pieces.append({
                'cut': stock_length,
                'effective': stock_length
            })
            remaining_length -= stock_length
            
            # Middle and final pieces
            while remaining_length > 0:
                piece_count += 1
                
                if remaining_length + lap_length <= stock_length:
                    # Final piece
                    pieces.append({
                        'cut': remaining_length + lap_length,
                        'effective': remaining_length
                    })
                    remaining_length = 0
                else:
                    # Middle piece
                    pieces.append({
                        'cut': stock_length,
                        'effective': stock_length - lap_length
                    })
                    remaining_length -= (stock_length - lap_length)
            
            total_pieces = len(pieces)
            splicing_info['additional_pieces'] += (total_pieces - 1) * quantity
            
            # Create individual items for each piece
            for idx, piece in enumerate(pieces, 1):
                processed_data.append({
                    'bar_mark': f"{bar_mark} ({idx}/{total_pieces})",
                    'diameter': diameter,
                    'cut_length': piece['cut'],
                    'quantity': quantity,
                    'note': f"Spliced from {bar_mark} (Lap: {lap_length:.3f}m)"
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
    
    Args:
        cutting_data: List of cutting requirements with bar_mark, diameter, cut_length, quantity
        stock_length: Standard stock length in meters
        cutting_tolerance_mm: Cutting tolerance in millimeters
        
    Returns:
        OptimizationResult with procurement summary and cutting plan
    """
    # Convert tolerance to meters
    cutting_tolerance = cutting_tolerance_mm / 1000.0
    
    # Group by diameter
    diameter_groups = {}
    for item in cutting_data:
        diameter = item['diameter']
        if diameter not in diameter_groups:
            diameter_groups[diameter] = []
        
        # Expand quantity into individual items
        for _ in range(item['quantity']):
            diameter_groups[diameter].append({
                'bar_mark': item['bar_mark'],
                'length': item['cut_length']
            })
    
    # Optimize each diameter group
    all_cutting_plans = []
    procurement_summary = []
    total_waste = 0
    total_stock_used = 0
    
    for diameter, items in diameter_groups.items():
        # Sort by length (descending) - First Fit Decreasing
        sorted_items = sorted(items, key=lambda x: x['length'], reverse=True)
        
        # Initialize stock bars
        stock_bars = []
        stock_counter = 1
        
        for item in sorted_items:
            item_length = item['length']
            placed = False
            
            # Try to fit in existing stock bars
            for stock in stock_bars:
                # Check if item fits (including cutting tolerance)
                space_needed = item_length
                if stock.cuts:  # Add tolerance if not the first cut
                    space_needed += cutting_tolerance
                
                if stock.remaining >= space_needed:
                    # Place item in this stock
                    stock.cuts.append({
                        'bar_mark': item['bar_mark'],
                        'length': item_length,
                        'start': stock_length - stock.remaining,
                        'end': stock_length - stock.remaining + item_length
                    })
                    stock.remaining -= space_needed
                    stock.utilization = ((stock_length - stock.remaining) / stock_length) * 100
                    placed = True
                    break
            
            # If not placed, create new stock bar
            if not placed:
                new_stock = StockBar(
                    stock_id=stock_counter,
                    diameter=diameter,
                    stock_length=stock_length,
                    cuts=[{
                        'bar_mark': item['bar_mark'],
                        'length': item_length,
                        'start': 0,
                        'end': item_length
                    }],
                    remaining=stock_length - item_length,
                    utilization=0
                )
                new_stock.utilization = ((stock_length - new_stock.remaining) / stock_length) * 100
                stock_bars.append(new_stock)
                stock_counter += 1
        
        # Calculate summary for this diameter
        total_bars = len(stock_bars)
        waste_for_diameter = sum(s.remaining for s in stock_bars)
        total_length_for_diameter = total_bars * stock_length
        waste_percentage = (waste_for_diameter / total_length_for_diameter * 100) if total_length_for_diameter > 0 else 0
        
        # Calculate weight
        unit_weight = WEIGHT_MAP.get(diameter, 0)  # Get weight per meter, default to 0 if not found
        total_weight_for_diameter = total_length_for_diameter * unit_weight
        
        procurement_summary.append({
            'diameter': diameter,
            'stock_length': stock_length,
            'quantity': total_bars,
            'total_length': total_length_for_diameter,
            'waste': waste_for_diameter,
            'waste_percentage': waste_percentage,
            'total_weight': total_weight_for_diameter
        })
        
        total_waste += waste_for_diameter
        total_stock_used += total_bars
        all_cutting_plans.extend(stock_bars)
    
    # Classify remnants
    reusable_remnants = []
    scrap_remnants = []
    total_weight_all = sum(item['total_weight'] for item in procurement_summary)
    
    for stock in all_cutting_plans:
        unit_weight = WEIGHT_MAP.get(stock.diameter, 0)
        remnant_weight = stock.remaining * unit_weight
        
        remnant_info = {
            'stock_id': stock.stock_id,
            'diameter': stock.diameter,
            'length': stock.remaining,
            'weight': remnant_weight
        }
        
        if stock.remaining >= 1.0:
            reusable_remnants.append(remnant_info)
        elif stock.remaining > 0:
            scrap_remnants.append(remnant_info)
    
    remnant_summary = {
        'reusable': reusable_remnants,
        'scrap': scrap_remnants
    }
    
    return OptimizationResult(
        procurement_summary=procurement_summary,
        cutting_plan=all_cutting_plans,
        total_waste=total_waste,
        total_stock_used=total_stock_used,
        remnant_summary=remnant_summary,
        total_weight=total_weight_all
)
