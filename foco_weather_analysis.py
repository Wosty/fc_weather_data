import pandas as ps
import numpy as np
import math

class WeatherAnalyzer:
    
    VALUE_AT_PERSONAL_THRESHOLD: float = 0.5
    FIELDS_EXPECTING_NO_TOLERANCE: list[str] = ['Precip','Wind_Dir','Gust_Dir']
    FIELDS_TO_DROP_WHEN_PERFORMING_CALCULATIONS: list[str] = ['Station']
    DAYTIME_SOLAR_RAD_THRESHOLD: float = 50

    class Preference:
        def __init__(self, dataSeries: str, min: float = None, max: float = None, ideal: float = None, tolerance: float = None):
            self.dataSeries = dataSeries
            self.min = min
            self.max = max
            self.ideal = ideal
            self.tolerance = tolerance

    def __init__(self, fileName: str):
        self.weather_data, self.units = self.file_setup(fileName)
        self.remove_invalid_data()
        self.weather_data.Date_and_Time = ps.to_datetime(self.weather_data.Date_and_Time, format='%m/%d/%Y %H:%M') \
            .dt.tz_localize('MST').dt.tz_convert('America/Denver')
        self.generate_weekly_daytime_hours()
        self.generate_daytime_dataframe()
        self.generate_general_preference_threshold()
    
    def file_setup(self, fileName):
        df = ps.read_csv(fileName, header=[0,1])
        df.rename(columns=lambda x: x.replace(' ', '_'), inplace=True)
        units = df.columns.get_level_values(1)
        df.columns = df.columns.get_level_values(0)
        return df, units
    
    def remove_invalid_data(self):
        thresholds, threshold_units = self.file_setup('thresholds.csv')
        for dataSeries in self.weather_data.columns:
            if self.units[self.weather_data.columns.get_loc(dataSeries)] == threshold_units[thresholds.columns.get_loc(dataSeries)]:
                ds = self.weather_data[dataSeries]
                if thresholds[dataSeries][0] != '*' and thresholds[dataSeries][1] != '*':
                    ds = ds.mask((ds < thresholds[dataSeries].min()) | (ds > thresholds[dataSeries].max())).dropna()
                elif thresholds[dataSeries][0] != '*':
                    ds = ds.mask(ds < thresholds[dataSeries].min()).dropna()
                elif thresholds[dataSeries][1] != '*':
                    ds = ds.mask(ds > thresholds[dataSeries].max()).dropna()
                self.weather_data[dataSeries] = ds
            else:
                print(f'WARNING: Unit mismatch for {dataSeries} in threshold check. Skipping.')
    
    def generate_weekly_daytime_hours(self):
        solar_rad_series = (self.weather_data[['Solar_Rad','Date_and_Time']].dropna()
            .groupby([self.weather_data.Date_and_Time.dt.isocalendar().week, self.weather_data.Date_and_Time.dt.hour])
                .Solar_Rad.agg('mean'))
        self.daytimeHoursByWeek: dict = {}
        for week in solar_rad_series.index.get_level_values(0):
            daytimeHours = solar_rad_series[week].mask(lambda x: x < self.DAYTIME_SOLAR_RAD_THRESHOLD).dropna()
            self.daytimeHoursByWeek[str(week)] = daytimeHours.index.values.tolist()

    def generate_daytime_dataframe(self):
        week_hour_groupby = self.weather_data.drop(columns=self.FIELDS_TO_DROP_WHEN_PERFORMING_CALCULATIONS).groupby([self.weather_data.Date_and_Time.dt.isocalendar().week, self.weather_data.Date_and_Time.dt.hour])
        self.daytime_df = ps.DataFrame()
        for (week, hour), group in week_hour_groupby:
            if str(week) in wa.daytimeHoursByWeek and hour in wa.daytimeHoursByWeek[str(week)]:
                self.daytime_df = ps.concat([self.daytime_df, group])

    def generate_general_preference_threshold(self):
        if self.daytimeHoursByWeek is None:
            self.generate_weekly_daytime_hours()
        if self.daytime_df is None:
            self.generate_daytime_dataframe()
        self.personal_enjoyment_thresholds: dict = {}
        for dataSeries in self.daytime_df.columns:
            pass
        
    def enjoyment_percentage_function(self, standardizedDistanceFromIdeal: float) -> float:
        standardizedDistanceFromIdeal = abs(standardizedDistanceFromIdeal)
        if (1 - (standardizedDistanceFromIdeal * (1 - self.VALUE_AT_PERSONAL_THRESHOLD)) <= 1):
            return 0
        return (math.log10(1 - (standardizedDistanceFromIdeal * (1 - self.VALUE_AT_PERSONAL_THRESHOLD))) + 1)

wa = WeatherAnalyzer('fcl01.csv')