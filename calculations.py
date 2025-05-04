from config import Config

class MaterialCalculator:
    @staticmethod
    def calculate_material(material_type, area, thickness=0):
        material = Config.MATERIALS.get(material_type.lower())
        if not material:
            return None
        
        # Коэффициенты расхода для разных материалов (кг/м² на 1 мм толщины)
        consumption_rates = {
            'штукатурка': 1.8,
            'стяжка': 2.0,
            'краска': 0.15,
            'затирка': 1.5,
            'наливной пол': 1.7,
            'кирпич': 50,  # шт/м²
            'гипсокартон': 0.1,  # листов/м²
            'плитка': 10,  # шт/м² (зависит от размера плитки)
            'обои': 0.05,  # рулонов/м²
            'лак': 0.1    # л/м²
        }
        
        rate = consumption_rates.get(material_type.lower(), 1)
        
        if material['thickness_dependent'] and thickness > 0:
            quantity = area * rate * thickness * Config.SAFETY_FACTOR
        else:
            quantity = area * rate * Config.SAFETY_FACTOR
        
        return round(quantity, 2)
    
    @staticmethod
    def format_calculation_result(material_type, area, thickness, quantity):
        material = Config.MATERIALS.get(material_type.lower())
        unit = material['unit'] if material else 'ед.'
        
        if material and material['thickness_dependent'] and thickness > 0:
            return (f"📊 Результат расчета:\n\n"
                    f"🧱 Материал: {material_type}\n"
                    f"📏 Площадь: {area} м²\n"
                    f"📐 Толщина слоя: {thickness} мм\n"
                    f"🧮 Необходимое количество: {quantity} {unit}\n\n"
                    f"ℹ️ С учетом коэффициента запаса {Config.SAFETY_FACTOR}")
        else:
            return (f"📊 Результат расчета:\n\n"
                    f"🧱 Материал: {material_type}\n"
                    f"📏 Площадь: {area} м²\n"
                    f"🧮 Необходимое количество: {quantity} {unit}\n\n"
                    f"ℹ️ С учетом коэффициента запаса {Config.SAFETY_FACTOR}")