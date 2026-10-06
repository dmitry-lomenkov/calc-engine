"""Сверка позиций карты с drikpanchang.com (эталоны зафиксированы вручную из Kundali).
Δ выводится в дуговых минутах. Запуск: python3 tests/compare_drikpanchang.py"""
import json, urllib.request

BASE = "http://127.0.0.1:8130"
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
         "Sagittarius","Capricorn","Aquarius","Pisces"]

def to_deg(sign, d, m, s):
    return SIGNS.index(sign)*30 + d + m/60 + s/3600

# эталоны drikpanchang: (sign, deg, min, sec)
REF = {
 "Москва 1985-06-15 14:30": {"input":{"date":"1985-06-15","time":"14:30","place":"Москва"},
   "p":{"Lagna":("Virgo",12,14,37),"Sun":("Gemini",0,36,1),"Moon":("Aries",26,13,43),
        "Mars":("Gemini",10,19,41),"Mercury":("Gemini",10,2,46),"Jupiter":("Capricorn",23,7,37),
        "Venus":("Aries",14,52,45),"Saturn":("Libra",29,3,4),"Rahu":("Aries",22,43,50),"Ketu":("Libra",22,43,50)}},
 "Ченнаи 1970-04-10 12:00": {"input":{"date":"1970-04-10","time":"12:00","place":"Ченнаи"},
   "p":{"Lagna":("Gemini",26,22,52),"Sun":("Pisces",26,31,44),"Moon":("Taurus",18,10,50),
        "Mars":("Taurus",0,40,3),"Mercury":("Aries",13,30,11),"Jupiter":("Libra",9,4,43),
        "Venus":("Aries",14,59,48),"Saturn":("Aries",15,47,47),"Rahu":("Aquarius",16,34,49),"Ketu":("Leo",16,34,49)}},
 "НСК 2011-06-01 12:00": {"input":{"date":"2011-06-01","time":"12:00","place":"Новосибирск"},
   "p":{"Lagna":("Leo",7,29,48),"Sun":("Taurus",16,22,1),"Moon":("Taurus",8,36,39),
        "Mars":("Aries",21,32,19),"Mercury":("Taurus",2,45,24),"Jupiter":("Aries",5,16,35),
        "Venus":("Aries",25,45,47),"Saturn":("Virgo",16,32,26),"Rahu":("Sagittarius",0,16,20),"Ketu":("Gemini",0,16,20)}},
 "Сидней 1990-01-15 08:00": {"input":{"date":"1990-01-15","time":"08:00","place":"Сидней"},
   "p":{"Lagna":("Capricorn",25,2,6),"Sun":("Capricorn",0,43,1),"Moon":("Leo",15,54,34),
        "Mars":("Scorpio",25,44,22),"Mercury":("Sagittarius",18,6,2),"Jupiter":("Gemini",9,42,55),
        "Venus":("Capricorn",7,19,46),"Saturn":("Sagittarius",23,30,58),"Rahu":("Capricorn",23,59,55),"Ketu":("Cancer",23,59,55)}},
 "НСК 2016-07-24 12:00": {"input":{"date":"2016-07-24","time":"12:00","place":"Новосибирск"},
   "p":{"Lagna":("Virgo",12,58,38),"Sun":("Cancer",7,38,6),"Moon":("Pisces",1,30,42),
        "Mars":("Scorpio",2,42,31),"Mercury":("Cancer",25,8,9),"Jupiter":("Leo",26,35,9),
        "Venus":("Cancer",20,37,22),"Saturn":("Scorpio",16,0,32),"Rahu":("Leo",20,38,51),"Ketu":("Aquarius",20,38,51)}},
}

def post(path, body):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def our_deg(planet, res):
    if planet == "Lagna":
        lg = res["lagna"]; return SIGNS.index(lg["rashi"])*30 + _dms(lg["longitude_dms"])
    g = next(x for x in res["grahas_d1"] if x["graha"]==planet)
    return SIGNS.index(g["rashi"])*30 + _dms(g["longitude_dms"])

def _dms(s):
    d,rest = s.split("°"); m,rest = rest.split("'"); sec = rest.replace('"','')
    return int(d)+int(m)/60+float(sec)/3600

for label, spec in REF.items():
    res = post("/v1/natal", spec["input"])
    print(f"\n=== {label} ===")
    print(f"  {'планета':<9}{'наш':>14}{'drikpanchang':>16}{'Δ (угл.мин)':>13}")
    maxd = 0
    for planet,(sg,d,m,s) in spec["p"].items():
        ref = to_deg(sg,d,m,s); ours = our_deg(planet,res)
        delta = ((ours-ref+180)%360-180)*60  # мин дуги
        if planet!="Lagna": maxd=max(maxd,abs(delta))
        flag = "" if abs(delta)<1 else ("  ⚠" if abs(delta)<2 else "  ❌")
        print(f"  {planet:<9}{ours%30:>13.4f}°{ref%30:>15.4f}°{delta:>12.2f}{flag}")
    print(f"  → макс Δ планет (без лагны): {maxd:.2f} угл.мин")
