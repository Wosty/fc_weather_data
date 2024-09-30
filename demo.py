from foco_weather_analysis import WeatherAnalyzer

wa = WeatherAnalyzer('fcl01.csv')

wa.add_factor_of_enjoyment('Air_Temp', 'RH')
wa.set_preference('Air_Temp', ideal=70, tolerance=10)
wa.set_preference('RH', ideal=.4, tolerance=.2)
wa.print_perfect_date()