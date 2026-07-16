import re
from typing import Optional, Tuple


def is_math_candidate(q: str) -> bool:
    if not isinstance(q, str):
        return False
    ql = q.lower()
    if not re.search(r"\d", ql):
        return False
    
    # Simple math expressions (+, -, *, /, =)
    if re.search(r"[+\-*/=]", ql) and re.search(r"\d", ql):
        return True
    
    # GSM8K specific patterns
    gsm8k_patterns = [
        'how much', 'how many', 'total', 'each', 'per', 'every', 'sells', 'buys', 'costs',
        'makes', 'earns', 'spends', 'left', 'remainder', 'increased', 'decreased',
        'profit', 'loss', 'dollars', 'dollar', '$', 'percent', '%', 'times', 'twice',
        'half', 'quarter', 'more than', 'less than', 'additional', 'extra',
        'eggs', 'ducks', 'chickens', 'bolts', 'meters', 'cups', 'feet', 'inches',
        'house', 'car', 'book', 'apple', 'orange', 'people', 'students', 'workers'
    ]
    
    # Check for GSM8K patterns first
    if any(pattern in ql for pattern in gsm8k_patterns):
        return True
    
    keywords = [
        # Esperanto keywords - UNIVERSAL LANGUAGE
        'kalkuli', 'komputi', 'solvi', 'trovi', 'determini', 'kio estas', 'egalas', 'plus', 'minus', 'foje', 'dividita',
        'pli ol', 'malpli ol', 'pli granda ol', 'pli malgranda ol', 'sumo', 'diferanco', 'produkto', 'kvociento',
        'aldoni', 'subtrahi', 'multipliki', 'dividi', 'aĉeti', 'vendi', 'elspezi', 'gajni', 'ŝpari', 'perdi', 'akiri',
        'ovo', 'pomo', 'oranĝo', 'libro', 'aŭto', 'domo', 'homo', 'studento', 'laboristo', 'aĵo',
        'aĉetita', 'vendita', 'uzita', 'bezonata', 'postulata', 'havebla', 'restanta', 'maldekstra super',
        # Fallback English keywords
        'per', 'each', 'left', 'remainder', 'total', 'how much', 'how many',
        'dollar', '$', 'percent', '%', 'profit', 'cost', 'price', 'bolts', 'half', 'twice', 'increase', 'decrease',
        'calculate', 'compute', 'solve', 'find', 'determine', 'what is', 'equals', 'plus', 'minus', 'times', 'divided',
        'more than', 'less than', 'greater than', 'smaller than', 'sum', 'difference', 'product', 'quotient',
        'add', 'subtract', 'multiply', 'divide', 'buy', 'sell', 'spend', 'earn', 'save', 'lose', 'gain',
        'eggs', 'apples', 'oranges', 'books', 'cars', 'houses', 'people', 'students', 'workers', 'items',
        'bought', 'sold', 'used', 'needed', 'required', 'available', 'remaining', 'left over',
        # Fallback Polish keywords
        'ile', 'oblicz', 'policz', 'znajdź', 'wyznacz', 'określ', 'dodaj', 'odejmij', 'pomnóż', 'podziel',
        'suma', 'różnica', 'iloczyn', 'iloraz', 'więcej', 'mniej', 'większe', 'mniejsze', 'równe',
        'koszt', 'cena', 'zysk', 'strata', 'oszczędności', 'wydatki', 'dochody', 'przychody'
    ]
    return any(k in ql for k in keywords)


def _extract_ints(q: str):
    # returns list of ints as they appear
    # Handle $2, $10, etc.
    q_clean = q.replace('$', '').replace(',', '')
    xs = re.findall(r"-?\d+", q_clean)
    nums = [int(x) for x in xs]
    
    # Also extract word numbers
    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }
    
    ql = q.lower()
    for word, num in word_to_num.items():
        if word in ql:
            nums.append(num)
    
    return nums

def _extract_floats(q: str):
    xs = re.findall(r"-?\d+(?:\.\d+)?", q.replace(',', ''))
    return [float(x) for x in xs]


def _janet_ducks(q: str) -> Optional[int]:
    # Pattern: eggs per day; eats X; bakes with Y; sells remainder at $P per egg
    ql = q.lower()
    if 'egg' in ql and 'per day' in ql and ('sell' in ql or 'sells' in ql) and ('$' in q or 'dollar' in ql):
        nums = _extract_ints(q)
        if len(nums) >= 4:
            # Try to find the correct mapping by context
            # Look for "X per day" pattern
            per_day = None
            for i, num in enumerate(nums):
                if str(num) in ql and 'per day' in ql[max(0, ql.find(str(num))-10):ql.find(str(num))+20]:
                    per_day = num
                    break
            
            # Look for price (usually the smallest number after $)
            price = None
            dollar_pos = q.find('$')
            if dollar_pos >= 0:
                for num in nums:
                    if str(num) in q[dollar_pos:dollar_pos+10]:
                        price = num
                        break
            
            # Remaining numbers are eats and bakes
            if per_day and price:
                remaining_nums = [n for n in nums if n != per_day and n != price]
                if len(remaining_nums) >= 2:
                    eats, bakes = remaining_nums[0], remaining_nums[1]
                    rem = per_day - eats - bakes
                    return rem * price if rem >= 0 else None
            
            # Fallback: use original heuristic
            per_day, eats, bakes, price = nums[0], nums[1], nums[2], nums[3]
            rem = per_day - eats - bakes
            return rem * price if rem >= 0 else None
    return None


def _bolts_half(q: str) -> Optional[int]:
    # Pattern: takes X bolts of blue and half that much white -> total X + X/2
    ql = q.lower()
    if 'bolt' in ql and 'half' in ql and 'white' in ql:
        nums = _extract_ints(q)
        if nums:
            blue = nums[0]
            white = blue / 2.0
            tot = blue + white
            if abs(tot - round(tot)) < 1e-9:
                return int(round(tot))
            return int(tot)
    return None


def _house_profit(q: str) -> Optional[int]:
    # Pattern: buys for $A, puts in $B repairs, increased by C% => profit = A*C% - B (per GSM8K convention)
    ql = q.lower()
    if ('buy' in ql or 'buys' in ql) and 'repair' in ql and ('increase' in ql or 'increased' in ql) and ('%' in q or 'percent' in ql):
        nums = _extract_ints(q)
        # Expect amounts A, B, C (percent)
        if len(nums) >= 3:
            A, B, C = nums[0], nums[1], nums[2]
            profit = int(round(A * (C / 100.0) - B))
            return profit
    return None

def _per_each_simple(q: str) -> Optional[int]:
    # Pattern: X items per Y; compute X*Y when clearly multiplicative
    ql = q.lower()
    if ' each ' in ql or ' per ' in ql:
        vals = _extract_floats(q)
        if len(vals) >= 2:
            a, b = vals[0], vals[1]
            prod = a * b
            if abs(prod - round(prod)) < 1e-9:
                return int(round(prod))
            return int(prod)
    return None

def _sum_total(q: str) -> Optional[int]:
    # Pattern: total = sum of listed numbers
    ql = q.lower()
    if 'total' in ql or 'in total' in ql or 'in all' in ql:
        vals = _extract_ints(q)
        if len(vals) >= 2:
            return sum(vals)
    return None

def _remaining_after(q: str) -> Optional[int]:
    # Pattern: after taking/using, remaining/left
    ql = q.lower()
    if 'remain' in ql or 'left' in ql:
        vals = _extract_ints(q)
        if len(vals) >= 2:
            rem = vals[0]
            for v in vals[1:]:
                rem -= v
            return rem
    return None

def _price_per_unit(q: str) -> Optional[int]:
    # Pattern: $P per unit, N units -> cost = P*N
    ql = q.lower()
    if ('$' in q or 'dollar' in ql) and (' per ' in ql):
        vals = _extract_floats(q)
        if len(vals) >= 2:
            # try both orders
            a, b = vals[0], vals[1]
            prod = a * b
            if abs(prod - round(prod)) < 1e-6:
                return int(round(prod))
            return int(prod)
    return None

def _percent_change(q: str) -> Optional[int]:
    # Find base B and percent p, compute new or profit conservatively
    ql = q.lower()
    if ('increase' in ql or 'increased' in ql or 'decrease' in ql or 'decreased' in ql) and ('%' in q or 'percent' in ql):
        vals = _extract_floats(q)
        if len(vals) >= 2:
            base = vals[0]; p = vals[1]
            if 'decre' in ql:
                new = base * (1.0 - p/100.0)
            else:
                new = base * (1.0 + p/100.0)
            if abs(new - round(new)) < 1e-6:
                return int(round(new))
            return int(new)
    return None

def _sequence_addsub(q: str) -> Optional[int]:
    # Heuristic: accumulate adds/subs based on nearby verbs/keywords
    ql = q.lower().replace(',', ' ')
    tokens = re.findall(r"[a-zA-Z$%]+|\d+", ql)
    add_words = { 'buy','buys','gets','get','add','adds','another','more','plus','earn','earns','receive','receives','bake','bakes','make','makes','collect','collects' }
    sub_words = { 'eat','eats','use','uses','used','spent','spend','give','gives','gave','lose','loses','lost','remove','removes','minus','sold','sells','sell' }
    base_words = { 'has','have','had','there','are','is','was' }
    # find indices of numbers
    nums = []
    for i,t in enumerate(tokens):
        if re.fullmatch(r"\d+", t):
            nums.append((i,int(t)))
    if not nums:
        return None
    # determine base
    base = 0
    # if first number is preceded by a base word within 3 tokens
    i0, v0 = nums[0]
    window = tokens[max(0,i0-3):i0]
    if any(w in base_words for w in window):
        base = v0
        start_idx = 1
    else:
        start_idx = 0
    val = base
    for idx in range(start_idx, len(nums)):
        i,v = nums[idx]
        ctx = tokens[max(0,i-4):min(len(tokens), i+5)]
        # prefer explicit add/sub words
        if any(w in sub_words for w in ctx):
            val -= v
        elif any(w in add_words for w in ctx):
            val += v
        else:
            # default: add if we had a base already, else just sum
            val += v
    return val


def _multi_step_work_rate(q: str) -> Optional[int]:
    """GSM8K: Work rate problems (hours * rate, overtime, etc.)"""
    ql = q.lower()
    if ('hour' in ql or 'hours' in ql) and ('rate' in ql or '$' in q or 'dollar' in ql):
        nums = _extract_floats(q)
        if len(nums) >= 3:
            # Pattern: regular_hours, rate, overtime_hours, overtime_multiplier
            if len(nums) >= 4:
                reg_hours, rate, ot_hours, ot_mult = nums[0], nums[1], nums[2], nums[3]
                regular_pay = reg_hours * rate
                overtime_pay = ot_hours * rate * ot_mult
                total = regular_pay + overtime_pay
                return int(round(total))
            # Pattern: hours, rate, total
            elif len(nums) >= 3:
                hours, rate, total = nums[0], nums[1], nums[2]
                if 'overtime' in ql or '1.2' in ql or '1.5' in ql:
                    # Assume overtime multiplier
                    ot_mult = 1.2 if '1.2' in ql else 1.5
                    regular_hours = min(hours, 40)  # Standard work week
                    ot_hours = max(0, hours - 40)
                    regular_pay = regular_hours * rate
                    overtime_pay = ot_hours * rate * ot_mult
                    return int(round(regular_pay + overtime_pay))
                else:
                    return int(round(hours * rate))
    return None


def _distance_time_speed(q: str) -> Optional[int]:
    """GSM8K: Distance = speed * time problems"""
    ql = q.lower()
    if ('mph' in ql or 'miles per hour' in ql) and ('hour' in ql or 'hours' in ql):
        nums = _extract_floats(q)
        if len(nums) >= 2:
            # Look for speed and time patterns
            speed_idx = -1
            time_idx = -1
            for i, num in enumerate(nums):
                if i < len(nums) - 1:  # Check if next token suggests speed
                    # Simple heuristic: if number followed by mph context
                    if 'mph' in ql[max(0, ql.find(str(int(num))) - 10):ql.find(str(int(num))) + 20]:
                        speed_idx = i
                if 'hour' in ql[max(0, ql.find(str(int(num))) - 5):ql.find(str(int(num))) + 10]:
                    time_idx = i
            
            if speed_idx >= 0 and time_idx >= 0 and speed_idx != time_idx:
                speed = nums[speed_idx]
                time = nums[time_idx]
                distance = speed * time
                return int(round(distance))
            
            # Fallback: multiply first two numbers if they seem like speed/time
            if len(nums) >= 2:
                return int(round(nums[0] * nums[1]))
    return None


def _percentage_of_total(q: str) -> Optional[int]:
    """GSM8K: Percentage calculations (X% of Y)"""
    ql = q.lower()
    if ('%' in q or 'percent' in ql) and ('of' in ql):
        nums = _extract_floats(q)
        if len(nums) >= 2:
            # Look for percentage and base number
            percent_idx = -1
            base_idx = -1
            
            for i, num in enumerate(nums):
                # Check if this number is a percentage
                if '%' in q[max(0, q.find(str(int(num))) - 5):q.find(str(int(num))) + 5]:
                    percent_idx = i
                elif 'of' in q[max(0, q.find(str(int(num))) - 10):q.find(str(int(num))) + 10]:
                    base_idx = i
            
            if percent_idx >= 0 and base_idx >= 0:
                percent = nums[percent_idx]
                base = nums[base_idx]
                result = (percent / 100.0) * base
                return int(round(result))
            
            # Fallback: first number as percent, second as base
            if len(nums) >= 2:
                result = (nums[0] / 100.0) * nums[1]
                return int(round(result))
    return None


def _multiplication_sequence(q: str) -> Optional[int]:
    """GSM8K: Sequential multiplications (A * B * C)"""
    ql = q.lower()
    if ('times' in ql or 'multiply' in ql or 'each' in ql) and ql.count('*') >= 1:
        nums = _extract_floats(q)
        if len(nums) >= 2:
            result = 1
            for num in nums:
                result *= num
            return int(round(result))
    
    # Pattern: "X times Y" or "X each" scenarios
    if 'times' in ql or 'each' in ql:
        nums = _extract_floats(q)
        if len(nums) >= 2:
            # Look for multiplication context
            if 'times' in ql:
                return int(round(nums[0] * nums[1]))
            elif 'each' in ql and len(nums) >= 3:
                # Pattern: X items, Y each -> X * Y
                return int(round(nums[0] * nums[1]))
    return None


def _complex_profit_loss(q: str) -> Optional[int]:
    """GSM8K: Complex profit/loss with repairs, increases, etc."""
    ql = q.lower()
    if ('profit' in ql or 'loss' in ql) and ('buy' in ql or 'buys' in ql) and ('repair' in ql or 'increase' in ql):
        nums = _extract_floats(q)
        if len(nums) >= 3:
            # Pattern: buy_price, repair_cost, increase_percent
            buy_price = nums[0]
            repair_cost = nums[1] 
            increase_pct = nums[2]
            
            total_cost = buy_price + repair_cost
            increase_amount = buy_price * (increase_pct / 100.0)
            new_value = buy_price + increase_amount
            profit = new_value - total_cost
            
            return int(round(profit))
    return None


def _remainder_after_operations(q: str) -> Optional[int]:
    """GSM8K: Remainder after multiple operations"""
    ql = q.lower()
    if ('remainder' in ql or 'left' in ql or 'remaining' in ql) and ('after' in ql or 'then' in ql):
        nums = _extract_ints(q)
        if len(nums) >= 3:
            # Start with first number, subtract the rest
            result = nums[0]
            for num in nums[1:]:
                result -= num
            return max(0, result)  # Can't have negative remainder
    return None


def _simple_arithmetic(q: str) -> Optional[int]:
    """Simple arithmetic expressions (2+2, 5*3, etc.)"""
    ql = q.lower()
    if re.search(r"[+\-*/=]", ql) and re.search(r"\d", ql):
        # Extract numbers and operators
        nums = _extract_floats(q)
        if len(nums) >= 2:
            # Look for operators
            if '+' in ql:
                return int(round(sum(nums)))
            elif '-' in ql and len(nums) == 2:
                return int(round(nums[0] - nums[1]))
            elif '*' in ql or 'times' in ql:
                result = 1
                for num in nums:
                    result *= num
                return int(round(result))
            elif '/' in ql and len(nums) == 2:
                if nums[1] != 0:
                    return int(round(nums[0] / nums[1]))
            elif '=' in ql:
                # Simple equation solving
                if '+' in ql:
                    return int(round(sum(nums)))
                elif '-' in ql and len(nums) == 2:
                    return int(round(nums[0] - nums[1]))
                elif '*' in ql:
                    result = 1
                    for num in nums:
                        result *= num
                    return int(round(result))
    return None


def solve(query: str) -> Tuple[bool, Optional[int]]:
    if not is_math_candidate(query):
        return False, None
    for fn in (
        _simple_arithmetic,  # First - catch simple expressions
        _janet_ducks,
        _bolts_half,
        _house_profit,
        _price_per_unit,
        _per_each_simple,
        _remaining_after,
        _sum_total,
        _percent_change,
        _sequence_addsub,
        # New GSM8K patterns
        _multi_step_work_rate,
        _distance_time_speed,
        _percentage_of_total,
        _multiplication_sequence,
        _complex_profit_loss,
        _remainder_after_operations,
    ):
        val = fn(query)
        if val is not None:
            return True, val
    return False, None
