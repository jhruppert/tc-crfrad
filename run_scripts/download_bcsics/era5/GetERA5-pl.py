import cdsapi

client = cdsapi.Client()

dataset = 'reanalysis-era5-pressure-levels'

request = {
        'product_type':['reanalysis'],
        'data_format':'grib',
        "download_format": "unarchived",
        'pressure_level':[
            '1','2','3',
            '5','7','10',
            '20','30','50',
            '70','100','125',
            '150','175','200',
            '225','250','300',
            '350','400','450',
            '500','550','600',
            '650','700','750',
            '775','800','825',
            '850','875','900',
            '925','950','975',
            '1000'
        ],
        "date": ["DATE-1/DATE-2"],
        # YY,
        # MM,
        # DD,
        # 'area':[Nort, West, Sout, East],
        'time':[
            "00:00", "01:00", "02:00",
            "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00",
            "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00",
            "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00",
            "21:00", "22:00", "23:00"
            ],
        'variable':[
            'geopotential','relative_humidity','specific_humidity',
            'temperature','u_component_of_wind','v_component_of_wind'
        ]
    }

client.retrieve(dataset, request, 'ERA5-DATE1-DATE2-pl.grib')
