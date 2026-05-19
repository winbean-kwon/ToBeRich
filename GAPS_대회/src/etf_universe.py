"""
제12회 GAPS ETF 유니버스 (2026-05-09 게시 기준)
총 188개 ETF, 10개 카테고리

is_risk=True  → 위험 자산 (최대 70% 제약)
is_risk=False → 안전 자산 (제한 없음)

category 분류:
  위험: fx_commodity, overseas_index, overseas_sector, domestic_index, domestic_sector
  안전: mmf_ultrashort, overseas_bond_corp, overseas_bond, domestic_bond_corp, domestic_bond
"""

ETF_LIST = [
    # ── FX 및 원자재 (위험) ──────────────────────────────────────────────────────
    {'ticker': '411060', 'name': 'ACE KRX금현물',             'aum': 52303,  'is_risk': True,  'category': 'fx_commodity'},
    {'ticker': '144600', 'name': 'KODEX 은선물(H)',             'aum': 14590,  'is_risk': True,  'category': 'fx_commodity'},
    {'ticker': '132030', 'name': 'KODEX 골드선물(H)',           'aum':  4821,  'is_risk': True,  'category': 'fx_commodity'},
    {'ticker': '261220', 'name': 'KODEX WTI원유선물(H)',        'aum':  1428,  'is_risk': True,  'category': 'fx_commodity'},
    {'ticker': '261240', 'name': 'KODEX 미국달러선물',          'aum':   724,  'is_risk': True,  'category': 'fx_commodity'},
    {'ticker': '292560', 'name': 'TIGER 일본엔선물',            'aum':   542,  'is_risk': True,  'category': 'fx_commodity'},
    {'ticker': '271060', 'name': 'KODEX 3대농산물선물(H)',      'aum':   252,  'is_risk': True,  'category': 'fx_commodity'},

    # ── 해외주식_지수 (위험) ──────────────────────────────────────────────────────
    {'ticker': '360750', 'name': 'TIGER 미국S&P500',                   'aum': 147821, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '379800', 'name': 'KODEX 미국S&P500',                   'aum':  81089, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '133690', 'name': 'TIGER 미국나스닥100',                 'aum':  79730, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '379810', 'name': 'KODEX 미국나스닥100',                 'aum':  55319, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '381180', 'name': 'TIGER 미국필라델피아반도체나스닥',     'aum':  34100, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '360200', 'name': 'ACE 미국S&P500',                     'aum':  33475, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '367380', 'name': 'ACE 미국나스닥100',                   'aum':  27323, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '379780', 'name': 'RISE 미국S&P500',                    'aum':  14147, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '371160', 'name': 'TIGER 차이나항셍테크',                'aum':   9134, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '449180', 'name': 'KODEX 미국S&P500(H)',                 'aum':   6946, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '251350', 'name': 'KODEX 선진국MSCI World',              'aum':   4913, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '448290', 'name': 'TIGER 미국S&P500TR(H)',               'aum':   4371, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '241180', 'name': 'TIGER 일본니케이225',                 'aum':   4279, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '453810', 'name': 'KODEX 인도Nifty50',                  'aum':   4103, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '453870', 'name': 'TIGER 인도니프티50',                  'aum':   3951, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '245710', 'name': 'ACE 베트남VN30(합성)',                'aum':   3155, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '448300', 'name': 'TIGER 미국나스닥100TR(H)',             'aum':   2963, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '283580', 'name': 'KODEX 차이나CSI300',                  'aum':   2825, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '200250', 'name': 'KIWOOM 인도Nifty50(합성)',            'aum':   2215, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '414780', 'name': 'TIGER 차이나과창판STAR50(합성)',       'aum':   2068, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '372330', 'name': 'KODEX 차이나항셍테크',                'aum':   1627, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '192090', 'name': 'TIGER 차이나CSI300',                  'aum':   1575, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '219480', 'name': 'KODEX 미국S&P500선물(H)',             'aum':   1437, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '245340', 'name': 'TIGER 미국다우존스30',                'aum':   1412, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '168580', 'name': 'ACE 중국본토CSI300',                  'aum':   1301, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '488500', 'name': 'TIGER 미국S&P500동일가중',             'aum':   1293, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '304940', 'name': 'KODEX 미국나스닥100선물(H)',           'aum':   1056, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '143850', 'name': 'TIGER 미국S&P500선물(H)',             'aum':    982, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '195980', 'name': 'PLUS 신흥국MSCI(합성 H)',             'aum':    920, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '101280', 'name': 'KODEX 일본TOPIX100',                  'aum':    624, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '099140', 'name': 'KODEX 차이나H',                       'aum':    437, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '245360', 'name': 'TIGER 차이나HSCEI',                   'aum':    400, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '238720', 'name': 'ACE 일본Nikkei225(H)',                'aum':    359, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '195930', 'name': 'TIGER 유로스탁스50(합성 H)',           'aum':    354, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '256440', 'name': 'ACE 인도네시아MSCI(합성)',             'aum':    345, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '280930', 'name': 'KODEX 미국러셀2000(H)',                'aum':    326, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '195970', 'name': 'PLUS 선진국MSCI(합성 H)',             'aum':    244, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '250730', 'name': 'RISE 차이나HSCEI(H)',                 'aum':    172, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '291130', 'name': 'ACE 멕시코MSCI(합성)',                'aum':    171, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '195920', 'name': 'TIGER 일본TOPIX(합성 H)',             'aum':    159, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '310080', 'name': 'RISE 중국MSCI China(H)',              'aum':    119, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '105010', 'name': 'TIGER 라틴35',                        'aum':    113, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '379790', 'name': 'RISE 유로스탁스50(H)',                'aum':    109, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '411860', 'name': 'KIWOOM 독일DAX',                      'aum':    104, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '499150', 'name': 'SOL 미국S&P500엔화노출(H)',            'aum':     85, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '189400', 'name': 'PLUS 글로벌MSCI(합성 H)',             'aum':     70, 'is_risk': True,  'category': 'overseas_index'},
    {'ticker': '261920', 'name': 'ACE 필리핀MSCI(합성)',                'aum':     57, 'is_risk': True,  'category': 'overseas_index'},

    # ── 해외주식_섹터 (위험) ──────────────────────────────────────────────────────
    {'ticker': '381170', 'name': 'TIGER 미국테크TOP10 INDXX',           'aum':  38009, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '458730', 'name': 'TIGER 미국배당다우존스',               'aum':  30379, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '487230', 'name': 'KODEX 미국AI전력핵심인프라',           'aum':  13631, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '371460', 'name': 'TIGER 차이나전기차SOLACTIVE',          'aum':  13027, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '457480', 'name': 'ACE 테슬라밸류체인액티브',             'aum':  11487, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '456600', 'name': 'TIME 글로벌AI인공지능액티브',          'aum':  10744, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '465580', 'name': 'ACE 미국빅테크TOP7 Plus',              'aum':   9716, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '446770', 'name': 'ACE 글로벌반도체TOP4 Plus',            'aum':   9671, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '446720', 'name': 'SOL 미국배당다우존스',                 'aum':   9140, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '497570', 'name': 'TIGER 미국필라델피아AI반도체나스닥',   'aum':   8188, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '402970', 'name': 'ACE 미국배당다우존스',                 'aum':   7817, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '390390', 'name': 'KODEX 미국반도체',                     'aum':   7809, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '452360', 'name': 'SOL 미국배당다우존스(H)',              'aum':   2026, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '182480', 'name': 'TIGER 미국MSCI리츠(합성 H)',           'aum':   1666, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '429000', 'name': 'TIGER 미국S&P500배당귀족',             'aum':   1556, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '463680', 'name': 'KODEX 미국S&P500테크놀로지',           'aum':    648, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '453640', 'name': 'KODEX 미국S&P500헬스케어',             'aum':    643, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '200030', 'name': 'KODEX 미국S&P500산업재(합성)',         'aum':    500, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '453650', 'name': 'KODEX 미국S&P500금융',                 'aum':    435, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '218420', 'name': 'KODEX 미국S&P500에너지(합성)',         'aum':    410, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '352560', 'name': 'KODEX 미국부동산리츠(H)',              'aum':    332, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '493420', 'name': 'SOL 미국배당다우존스TR',               'aum':    325, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '287180', 'name': 'PLUS 미국나스닥테크',                  'aum':    316, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '245350', 'name': 'TIGER 유로스탁스배당30',               'aum':    296, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '494410', 'name': 'PLUS 미국S&P500성장주',               'aum':    287, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '460660', 'name': 'RISE 미국S&P배당킹',                   'aum':    245, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '185680', 'name': 'KODEX 미국S&P바이오(합성)',            'aum':    200, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '453630', 'name': 'KODEX 미국S&P500필수소비재',           'aum':    176, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '463640', 'name': 'KODEX 미국S&P500유틸리티',             'aum':    162, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '453660', 'name': 'KODEX 미국S&P500경기소비재',           'aum':    139, 'is_risk': True,  'category': 'overseas_sector'},
    {'ticker': '463690', 'name': 'KODEX 미국S&P500커뮤니케이션',         'aum':    131, 'is_risk': True,  'category': 'overseas_sector'},

    # ── 국내주식_지수 (위험) ──────────────────────────────────────────────────────
    {'ticker': '069500', 'name': 'KODEX 200',          'aum': 164803, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '229200', 'name': 'KODEX 코스닥150',    'aum':  71839, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '102110', 'name': 'TIGER 200',          'aum':  67897, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '278530', 'name': 'KODEX 200TR',        'aum':  52559, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '310970', 'name': 'TIGER MSCI Korea TR','aum':  39380, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '148020', 'name': 'RISE 200',           'aum':  29007, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '232080', 'name': 'TIGER 코스닥150',    'aum':  22098, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '278540', 'name': 'KODEX MSCI Korea TR','aum':  21216, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '294400', 'name': 'KIWOOM 200TR',       'aum':  15375, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '152100', 'name': 'PLUS 200',           'aum':  13051, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '226490', 'name': 'KODEX 코스피',       'aum':   7939, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '361580', 'name': 'RISE 200TR',         'aum':   3842, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '277630', 'name': 'TIGER 코스피',       'aum':   3810, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '295040', 'name': 'SOL 200TR',          'aum':   3540, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '302450', 'name': 'RISE 코스피',        'aum':   3310, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '328370', 'name': 'PLUS 코스피TR',      'aum':   1070, 'is_risk': True,  'category': 'domestic_index'},
    {'ticker': '156080', 'name': 'KODEX MSCI Korea',   'aum':    294, 'is_risk': True,  'category': 'domestic_index'},

    # ── 국내주식_섹터 (위험) ──────────────────────────────────────────────────────
    {'ticker': '091160', 'name': 'KODEX 반도체',                  'aum':  36019, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '161510', 'name': 'PLUS 고배당주',                  'aum':  23624, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '102780', 'name': 'KODEX 삼성그룹',                 'aum':  23508, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '395160', 'name': 'KODEX AI반도체',                 'aum':  20947, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '466920', 'name': 'SOL 조선TOP3플러스',             'aum':  18733, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '305720', 'name': 'KODEX 2차전지산업',              'aum':  18187, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '449450', 'name': 'PLUS K방산',                     'aum':  17803, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '487240', 'name': 'KODEX AI전력핵심설비',           'aum':  15914, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '395270', 'name': 'HANARO Fn K-반도체',             'aum':  14664, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '315930', 'name': 'KODEX Top5PlusTR',               'aum':  13675, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '305540', 'name': 'TIGER 2차전지테마',              'aum':  11376, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '494670', 'name': 'TIGER 조선TOP10',                'aum':   9938, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '445290', 'name': 'KODEX 로봇액티브',               'aum':   9793, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '455850', 'name': 'SOL AI반도체소부장',              'aum':   9687, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '466940', 'name': 'TIGER 은행고배당플러스TOP10',     'aum':   9364, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '463250', 'name': 'TIGER K방산&우주',               'aum':   8830, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139260', 'name': 'TIGER 200 IT',                   'aum':   8199, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '462010', 'name': 'TIGER 2차전지소재Fn',            'aum':   7840, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '434730', 'name': 'HANARO 원자력iSelect',           'aum':   7364, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '091180', 'name': 'KODEX 자동차',                   'aum':   5224, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '091170', 'name': 'KODEX 은행',                     'aum':   4569, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139230', 'name': 'TIGER 200 중공업',               'aum':   3928, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '325010', 'name': 'KODEX 성장주',                   'aum':   1495, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '363580', 'name': 'KODEX 200IT TR',                 'aum':   1021, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139220', 'name': 'TIGER 200 건설',                 'aum':    491, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139270', 'name': 'TIGER 200 금융',                 'aum':    430, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '227540', 'name': 'TIGER 200 헬스케어',             'aum':    316, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '147970', 'name': 'TIGER 모멘텀',                   'aum':    294, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139250', 'name': 'TIGER 200 에너지화학',           'aum':    288, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '174350', 'name': 'TIGER 로우볼',                   'aum':     94, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '227550', 'name': 'TIGER 200 산업재',               'aum':     91, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '227570', 'name': 'TIGER 우량가치',                 'aum':     88, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139290', 'name': 'TIGER 200 경기소비재',           'aum':     83, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '139240', 'name': 'TIGER 200 철강소재',             'aum':     72, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '315270', 'name': 'TIGER 200커뮤니케이션서비스',    'aum':     66, 'is_risk': True,  'category': 'domestic_sector'},
    {'ticker': '227560', 'name': 'TIGER 200 생활소비재',           'aum':     42, 'is_risk': True,  'category': 'domestic_sector'},

    # ── 금리연계형/초단기채권 (안전) ───────────────────────────────────────────────
    {'ticker': '459580', 'name': 'KODEX CD금리액티브(합성)',        'aum':  79731, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '488770', 'name': 'KODEX 머니마켓액티브',            'aum':  72891, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '423160', 'name': 'KODEX KOFR금리액티브(합성)',      'aum':  43045, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '455890', 'name': 'RISE 머니마켓액티브',             'aum':  22406, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '469830', 'name': 'SOL 초단기채권액티브',            'aum':   9092, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '153130', 'name': 'KODEX 단기채권',                  'aum':   7321, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '456610', 'name': 'TIGER 미국달러SOFR금리액티브(합성)','aum':  6550, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '196230', 'name': 'RISE 단기통안채',                 'aum':   2081, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '455960', 'name': 'RISE 미국달러SOFR금리액티브(합성)','aum':   602, 'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '468370', 'name': 'KODEX iShares미국인플레이션국채액티브','aum': 187,'is_risk': False, 'category': 'mmf_ultrashort'},
    {'ticker': '430500', 'name': 'KIWOOM 물가채KIS',                'aum':    113, 'is_risk': False, 'category': 'mmf_ultrashort'},

    # ── 해외채권_회사채 (안전) ──────────────────────────────────────────────────────
    {'ticker': '458260', 'name': 'TIGER 미국투자등급회사채액티브(H)','aum':  2883, 'is_risk': False, 'category': 'overseas_bond_corp'},
    {'ticker': '468380', 'name': 'KODEX iShares미국하이일드액티브',  'aum':  1160, 'is_risk': False, 'category': 'overseas_bond_corp'},
    {'ticker': '455660', 'name': 'ACE 미국하이일드액티브(H)',         'aum':   528, 'is_risk': False, 'category': 'overseas_bond_corp'},
    {'ticker': '468630', 'name': 'KODEX iShares미국투자등급회사채액티브','aum':367,'is_risk': False, 'category': 'overseas_bond_corp'},
    {'ticker': '332620', 'name': 'PLUS 미국장기우량회사채',          'aum':   208, 'is_risk': False, 'category': 'overseas_bond_corp'},
    {'ticker': '332610', 'name': 'PLUS 미국단기회사채(AAA~A)',       'aum':   131, 'is_risk': False, 'category': 'overseas_bond_corp'},
    {'ticker': '182490', 'name': 'TIGER 단기선진하이일드(합성 H)',   'aum':    82, 'is_risk': False, 'category': 'overseas_bond_corp'},

    # ── 해외채권_종합 (안전) ──────────────────────────────────────────────────────
    {'ticker': '453850', 'name': 'ACE 미국30년국채액티브(H)',                 'aum': 18200, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '458250', 'name': 'TIGER 미국30년국채스트립액티브(합성 H)',    'aum':  6231, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '484790', 'name': 'KODEX 미국30년국채액티브(H)',               'aum':  5934, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '329750', 'name': 'TIGER 미국달러단기채권액티브',              'aum':  4708, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '472870', 'name': 'RISE 미국30년국채엔화노출(합성 H)',         'aum':  3570, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '476760', 'name': 'ACE 미국30년국채액티브',                    'aum':  3171, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '305080', 'name': 'TIGER 미국채10년선물',                      'aum':  2446, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '308620', 'name': 'KODEX 미국10년국채선물',                    'aum':  1138, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '476750', 'name': 'ACE 미국30년국채엔화노출액티브(H)',          'aum':   860, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '489000', 'name': 'PLUS 일본엔화초단기국채(합성)',              'aum':   219, 'is_risk': False, 'category': 'overseas_bond'},
    {'ticker': '267440', 'name': 'RISE 미국장기국채선물(H)',                   'aum':    51, 'is_risk': False, 'category': 'overseas_bond'},

    # ── 국내채권_회사채 (안전) ──────────────────────────────────────────────────────
    {'ticker': '273130', 'name': 'KODEX 종합채권(AA-이상)액티브',        'aum': 38484, 'is_risk': False, 'category': 'domestic_bond_corp'},
    {'ticker': '385540', 'name': 'RISE 종합채권(A-이상)액티브',          'aum': 17737, 'is_risk': False, 'category': 'domestic_bond_corp'},
    {'ticker': '0061Z0', 'name': 'RISE 단기특수은행채액티브',             'aum': 12843, 'is_risk': False, 'category': 'domestic_bond_corp', 'special_ticker': True},
    {'ticker': '451540', 'name': 'TIGER 종합채권(AA-이상)액티브',        'aum': 10134, 'is_risk': False, 'category': 'domestic_bond_corp'},
    {'ticker': '438330', 'name': 'TIGER 투자등급회사채액티브',           'aum':  6984, 'is_risk': False, 'category': 'domestic_bond_corp'},
    {'ticker': '0016X0', 'name': 'SOL 중단기회사채(A-이상)액티브',       'aum':  3669, 'is_risk': False, 'category': 'domestic_bond_corp', 'special_ticker': True},
    {'ticker': '363570', 'name': 'KODEX 장기종합채권(AA-이상)액티브',    'aum':  3200, 'is_risk': False, 'category': 'domestic_bond_corp'},
    {'ticker': '278620', 'name': 'PLUS 단기채권액티브',                  'aum':   532, 'is_risk': False, 'category': 'domestic_bond_corp'},
    {'ticker': '336160', 'name': 'RISE 금융채액티브',                    'aum':   417, 'is_risk': False, 'category': 'domestic_bond_corp'},

    # ── 국내채권_종합 (안전) ──────────────────────────────────────────────────────
    {'ticker': '157450', 'name': 'TIGER 단기통안채',          'aum':  9750, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '114260', 'name': 'KODEX 국고채3년',           'aum':  5353, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '148070', 'name': 'KIWOOM 국고채10년',         'aum':  4925, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '439870', 'name': 'KODEX 국고채30년액티브',    'aum':  3549, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '302190', 'name': 'TIGER 중장기국채',          'aum':  2950, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '272560', 'name': 'RISE 단기국공채액티브',     'aum':  1915, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '114100', 'name': 'RISE 국고채3년',            'aum':  1798, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '451530', 'name': 'TIGER 국고채30년스트립액티브','aum': 1444, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '298340', 'name': 'PLUS 국채선물3년',          'aum':   600, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '426150', 'name': 'WON 대한민국국고채액티브',  'aum':   530, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '152380', 'name': 'KODEX 국채선물10년',        'aum':   402, 'is_risk': False, 'category': 'domestic_bond'},
    {'ticker': '397420', 'name': 'RISE 국채선물5년추종',      'aum':    52, 'is_risk': False, 'category': 'domestic_bond'},
]

# ── 헬퍼 함수 ────────────────────────────────────────────────────────────────────

import pandas as pd

CATEGORY_LABELS = {
    'fx_commodity':       'FX 및 원자재',
    'overseas_index':     '해외주식_지수',
    'overseas_sector':    '해외주식_섹터',
    'domestic_index':     '국내주식_지수',
    'domestic_sector':    '국내주식_섹터',
    'mmf_ultrashort':     '금리연계형/초단기채권',
    'overseas_bond_corp': '해외채권_회사채',
    'overseas_bond':      '해외채권_종합',
    'domestic_bond_corp': '국내채권_회사채',
    'domestic_bond':      '국내채권_종합',
}

RISK_CATEGORIES  = ['fx_commodity', 'overseas_index', 'overseas_sector', 'domestic_index', 'domestic_sector']
SAFE_CATEGORIES  = ['mmf_ultrashort', 'overseas_bond_corp', 'overseas_bond', 'domestic_bond_corp', 'domestic_bond']


def to_dataframe() -> pd.DataFrame:
    return pd.DataFrame(ETF_LIST)


def get_tickers(category: str = None, is_risk: bool = None, exclude_special: bool = True) -> list:
    result = ETF_LIST
    if category:
        result = [e for e in result if e['category'] == category]
    if is_risk is not None:
        result = [e for e in result if e['is_risk'] == is_risk]
    if exclude_special:
        result = [e for e in result if not e.get('special_ticker', False)]
    return [e['ticker'] for e in result]


def get_special_tickers() -> list:
    return [e for e in ETF_LIST if e.get('special_ticker', False)]


def summary():
    df = to_dataframe()
    print(f"총 ETF 수: {len(df)}개")
    print(f"  위험자산: {df['is_risk'].sum()}개")
    print(f"  안전자산: {(~df['is_risk']).sum()}개")
    print(f"  특수 티커: {df.get('special_ticker', pd.Series([False]*len(df))).sum()}개\n")
    for cat, label in CATEGORY_LABELS.items():
        cnt = (df['category'] == cat).sum()
        print(f"  {label:<25s}: {cnt:3d}개")


if __name__ == '__main__':
    summary()
