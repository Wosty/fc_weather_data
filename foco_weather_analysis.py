import pandas as ps

class weather_analyzer:
    
    DAYTIME_SOLAR_RAD_THRESHOLD: float = 50

    def __init__(self, fileName: str):
        self.weather_data, self.units = self.File_Clean_Up(fileName)
        self.Remove_Invalid_Data()
        self.weather_data.Date_and_Time = ps.to_datetime(self.weather_data.Date_and_Time, format='%m/%d/%Y %H:%M').dt.tz_localize('MST').dt.tz_convert('America/Denver')
    
    def Generate_General_Preferences(self):
        pass

    def GetWeeklyDaytimeHours(self):
        solar_rad_series = (self.weather_data[['Solar_Rad','Date_and_Time']].dropna()
            .groupby([self.weather_data.Date_and_Time.dt.isocalendar().week, self.weather_data.Date_and_Time.dt.hour])
                .Solar_Rad.agg('mean'))
        daytimeHoursByWeek: dict = {}
        for week in solar_rad_series.index.get_level_values(0):
            weeklyDaytimeHours = solar_rad_series[week].mask(lambda x: x < self.DAYTIME_SOLAR_RAD_THRESHOLD).dropna()
            daytimeHoursByWeek[week] = (weeklyDaytimeHours.index[0] - 1, weeklyDaytimeHours.index[-1] + 1)

    def File_Clean_Up(self, fileName):
        df = ps.read_csv(fileName, header=[0,1])
        df.rename(columns=lambda x: x.replace(' ', '_'), inplace=True)
        units = df.columns.get_level_values(1)
        df.columns = df.columns.get_level_values(0)
        return df, units

    def Remove_Invalid_Data(self):
        thresholds, threshold_units = self.File_Clean_Up('thresholds.csv')
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

    def CalculatePersonalTolerance(self, ):
        pass

    def GetEnjoymentOfDays(self, min: float, max: float):
        pass
    
    def GetEnjoymentRange(self, ideal: float, tolerance: float = None):
        pass

    def GetEnjoymentSeriesByWeek(self, seriesName:str, min: float, max: float):
        pass

    def GetEnjoymentSeriesByDay(self, seriesName:str, min: float, max: float):
        pass
    
    def GetEnjoymentSeries(self, df:ps.DataFrame, min:float, max: float):
        pass

    def GetPerfectDate():
        pass

