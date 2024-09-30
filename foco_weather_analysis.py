import pandas as ps
import numpy as np
import math
from datetime import datetime, timedelta
import calendar

class WeatherAnalyzer:

    VALUE_AT_PERSONAL_TOLERANCE: float = 0.9
    FIELDS_EXPECTING_NO_TOLERANCE: set = {'Precip','Wind_Dir','Gust_Dir'}
    FIELDS_TO_DROP_WHEN_PERFORMING_CALCULATIONS: set = {'Station'}
    DAYTIME_SOLAR_RAD_THRESHOLD: float = 50

    class Preference:
        def __init__(self, data_series: str, ideal: float = None, tolerance: float = None):
            self.data_series = data_series
            self.ideal = ideal
            self.tolerance = tolerance

    def __init__(self, fileName: str):
        self.weather_data, self.units = self.file_setup(fileName)
        self.remove_invalid_data()
        self.weather_data.Date_and_Time = ps.to_datetime(self.weather_data.Date_and_Time, format='%m/%d/%Y %H:%M') \
            .dt.tz_localize('MST').dt.tz_convert('America/Denver')
        self.generate_weekly_daytime_hours()
        self.generate_daytime_dataframe()
        self.generate_general_preference()
        self.factors_of_enjoyment: set = set()
    
    def file_setup(self, fileName):
        df = ps.read_csv(fileName, header=[0,1])
        df.rename(columns=lambda x: x.replace(' ', '_'), inplace=True)
        units = df.columns.get_level_values(1)
        df.columns = df.columns.get_level_values(0)
        return df, units
    
    def remove_invalid_data(self):
        thresholds, threshold_units = self.file_setup('thresholds.csv')
        for data_series in self.weather_data.columns:
            if self.units[self.weather_data.columns.get_loc(data_series)] == threshold_units[thresholds.columns.get_loc(data_series)]:
                ds = self.weather_data[data_series]
                if thresholds[data_series][0] != '*' and thresholds[data_series][1] != '*':
                    ds = ds.mask((ds < thresholds[data_series].min()) | (ds > thresholds[data_series].max())).dropna()
                elif thresholds[data_series][0] != '*':
                    ds = ds.mask(ds < thresholds[data_series].min()).dropna()
                elif thresholds[data_series][1] != '*':
                    ds = ds.mask(ds > thresholds[data_series].max()).dropna()
                self.weather_data[data_series] = ds
            else:
                print(f'WARNING: Unit mismatch for {data_series} in threshold check. Skipping.')
    
    def generate_weekly_daytime_hours(self):
        solar_rad_series = (self.weather_data[['Solar_Rad','Date_and_Time']].dropna()
            .groupby([self.weather_data.Date_and_Time.dt.isocalendar().week, self.weather_data.Date_and_Time.dt.hour])
                .Solar_Rad.agg('mean'))
        self.daytime_hours_by_week: dict = {}
        for week in solar_rad_series.index.get_level_values(0):
            daytime_hours = solar_rad_series[week].mask(lambda x: x < self.DAYTIME_SOLAR_RAD_THRESHOLD).dropna()
            self.daytime_hours_by_week[str(week)] = daytime_hours.index.values.tolist()

    def generate_daytime_dataframe(self):
        if self.daytime_hours_by_week is None:
            self.generate_weekly_daytime_hours()
        week_hour_groupby = self.weather_data.drop(columns=self.FIELDS_TO_DROP_WHEN_PERFORMING_CALCULATIONS, errors='ignore').groupby([self.weather_data.Date_and_Time.dt.isocalendar().week, self.weather_data.Date_and_Time.dt.hour])
        self.daytime_df = ps.DataFrame()
        for (week, hour), group in week_hour_groupby:
            if str(week) in self.daytime_hours_by_week and hour in self.daytime_hours_by_week[str(week)]:
                self.daytime_df = ps.concat([self.daytime_df, group])

    def generate_general_preference(self):
        if self.daytime_df is None:
            self.generate_daytime_dataframe()
        self.personal_enjoyment_preferences: dict = {}
        datetime_indexed_df = self.daytime_df.set_index('Date_and_Time')
        for data_series in datetime_indexed_df.drop(columns=(self.FIELDS_TO_DROP_WHEN_PERFORMING_CALCULATIONS.union(self.FIELDS_EXPECTING_NO_TOLERANCE)), errors='ignore').columns:
            series_preference = self.Preference(data_series)
            series_preference.tolerance = datetime_indexed_df[data_series].groupby(datetime_indexed_df.index.day_of_year).std().mean() / 2
            series_preference.ideal = datetime_indexed_df[data_series].mean()
            self.personal_enjoyment_preferences[data_series] = series_preference

    def set_preference(self, data_series: str, ideal: float, tolerance: float):
        if self.validate_data_series(data_series):
            self.personal_enjoyment_preferences[data_series].ideal = ideal
            self.personal_enjoyment_preferences[data_series].tolerance = tolerance
    
    def set_preference_with_max_and_min(self, data_series: str, max: float, min: float):
        if max < min:
            temp = max
            max = min
            min = temp
            print('Min should not be greater than max')
        if max == min:
            max = max + self.personal_enjoyment_preferences[data_series].tolerance
            min = min - self.personal_enjoyment_preferences[data_series].tolerance
            print('You should be more tolerant')
        if self.validate_data_series(data_series):
            self.personal_enjoyment_preferences[data_series].ideal = (max + min) / 2
            self.personal_enjoyment_preferences[data_series].tolerance = (max - min) / 2

    def add_factor_of_enjoyment(self, *data_seriesList: str):
        for data_series in data_seriesList:
            if self.validate_data_series(data_series):
                self.factors_of_enjoyment.add(data_series)
    
    def remove_factor_of_enjoyment(self, *data_seriesList: str):
        for data_series in data_seriesList:
            if self.validate_data_series(data_series):
                self.factors_of_enjoyment.discard(data_series)

    def validate_data_series(self, data_series: str) -> bool:
        if data_series in self.weather_data.columns:
            return True
        else:
            print(f'ERROR: {data_series} not found in weather data')
            return False

    def generate_enjoyment_dataframe(self):
        if self.daytime_df is None:
            self.generate_daytime_dataframe()
        datetime_indexed_factors_of_enjoyment_df = self.daytime_df.set_index('Date_and_Time').drop(columns=([x for x in self.weather_data.columns if x not in self.factors_of_enjoyment]), errors='ignore')
        self.enjoyment_df_with_factors_of_enjoyment = ps.DataFrame(index=datetime_indexed_factors_of_enjoyment_df.index)
        for data_series in datetime_indexed_factors_of_enjoyment_df:
            factordata_series = datetime_indexed_factors_of_enjoyment_df[data_series].dropna().map(lambda x: self.enjoyment_percentage_function(data_series, x))
            self.enjoyment_df_with_factors_of_enjoyment = ps.concat([self.enjoyment_df_with_factors_of_enjoyment, factordata_series])
        
    def enjoyment_percentage_function(self, data_series: str, value: float) -> float:
        standardized_distance_from_ideal = abs((value - self.personal_enjoyment_preferences[data_series].ideal) / self.personal_enjoyment_preferences[data_series].tolerance) 
        if (1 - (standardized_distance_from_ideal * (1 - self.VALUE_AT_PERSONAL_TOLERANCE)) <= 0):
            return 0
        return (math.log10(1 - (standardized_distance_from_ideal * (1 - self.VALUE_AT_PERSONAL_TOLERANCE))) + 1)

    def generate_daily_enjoyment_dataframe(self):
        if self.enjoyment_df_with_factors_of_enjoyment is None:
            self.generate_enjoyment_dataframe()
        self.daily_enjoyment = ps.Series(np.ones(366))
        for data_series in self.enjoyment_df_with_factors_of_enjoyment.columns:
            data_series_from_enjoyment_df = self.enjoyment_df_with_factors_of_enjoyment[data_series].dropna()
            self.daily_enjoyment = self.daily_enjoyment.multiply(data_series_from_enjoyment_df.groupby(data_series_from_enjoyment_df.index.dayofyear).agg('mean'))

    def find_perfect_date(self):
        self.generate_enjoyment_dataframe()
        self.generate_daily_enjoyment_dataframe()
        return (self.daily_enjoyment.idxmax(), self.daily_enjoyment.max())
    
    def print_perfect_date(self):
        (perfect_date, enjoyment) = self.find_perfect_date()
        perfect_date = int(perfect_date)
        date = datetime(datetime.now().year, 1, 1) + timedelta(days=perfect_date - 1)
        print(f'Your perfect date is {calendar.month_name[date.month]} {date.day}.')
        print(f'Based only on historical data, we think you have a {enjoyment * 100:.2f}% chance of enjoying that day.')

