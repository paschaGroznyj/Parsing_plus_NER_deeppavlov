import pandas as pd
from processing import Processing

pr = Processing()
path = ".../analyzer_analyzer_urls.csv"

data = pd.read_csv(path, index_col=False)
data.columns = ['url', 'html']

print(len(data['url'].unique()))  # 7788

header = ['url', 'html']

for i in range(pr.n_for_range):
    start, stop = i * pr.step, (i + 1) * pr.step

    data_ = data.iloc[start:stop]
    data_.columns = header  # Для каждого piece свой заголовок
    data_.to_csv(f'pieces/piece_{start}_{stop}.csv', index=False)