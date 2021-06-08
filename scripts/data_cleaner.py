import pandas as pd
import json
import re
import gender_guesser.detector as gender

regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
CONFIG_PATH = 'data/config/config.json'
detector = gender.Detector()


def get_gender(name):
    gender_guess = detector.get_gender(u'' + name.capitalize())
    if gender_guess == "unknown" or gender_guess == "andy":
        return 'Monsieur'
    if gender_guess == "female" or "mostly_female":
        return "Madame"
    return "Monsieur"


def check(email):
    if(re.search(regex, email)):
        return True

    else:
        return False


class DataCleaner:
    def __init__(self, file_name, file_type='csv', columns=[], email_column='', merge_columns=[], rename_columns=None):
        self.file_name = file_name
        self.file_type = file_type
        self.df = None
        self.relevant_columns = columns
        self.email_column = email_column
        self.merge_columns = merge_columns
        self.rename_columns = rename_columns

    def keep_relevant_columns(self):
        self.df = self.df[self.relevant_columns]

    def load(self):
        if self.file_type == 'csv':
            self.df = pd.read_csv(self.file_name)
        if self.file_type == 'xls' or self.file_type == 'xlsx':
            self.df = pd.read_excel(self.file_name, sheet_name=None)['Sheet3']

    def remove_empty_data(self):
        self.df = self.df.dropna()
        return

    def remove_email_duplicate(self):
        self.df = self.df.drop_duplicates(subset=[self.email_column])
        return

    def normalize_columns(self):
        """ pre-process text data :
          * lower case
          * remove ponctuation
          * strip
        """
        for column in self.relevant_columns:
            self.df[column] = self.df[column].str.lower()
            self.df[column] = self.df[column].str.strip()
            self.df[column] = self.df[column].str.replace(
                '&', ' and ')
            self.df[column] = self.df[column].str.replace(
                ',', ' ')

    def correct_email_column(self):
        """ email has to be valid / well formatted """
        self.df[self.email_column] = self.df[self.email_column].str.replace(
            'mailto:', '')
        self.df['is_valid_email'] = self.df[self.email_column].apply(
            lambda x: check(x))
        self.df[self.email_column] = self.df[self.email_column][self.df['is_valid_email']]
        self.df.pop('is_valid_email')

    def clean(self):
        self.load()
        self.keep_relevant_columns()
        self.normalize_columns()
        self.remove_email_duplicate()
        self.remove_empty_data()
        self.correct_email_column()
        self.merge()
        self.rename()
        self.remove_empty_data()

    def merge(self):
        """ merge two columns into one since they can express the same information """
        for item_merge in self.merge_columns:
            new_column_name = item_merge['merged_name']
            self.df[new_column_name] = self.df[item_merge['columns'][0]].str.cat(
                self.df[item_merge['columns'][1]], sep=" ")
            self.df.pop(item_merge['columns'][0])
            self.df.pop(item_merge['columns'][1])

    def rename(self):
        self.df = self.df.rename(columns=self.rename_columns)


class DataIterator:
    def __init__(self, config_file):
        with open(config_file, "r") as config:
            self.config = json.load(config)
        self.datasets = []
        self.final_dataset = None

    def iterate(self):
        for item in self.config['dataset']:
            self.datasets.append(
                DataCleaner(
                    file_name=item['file_name'],
                    file_type=item['file_type'],
                    columns=item['relevant_columns'],
                    email_column=item['email_column'],
                    merge_columns=item['merge_columns'],
                    rename_columns=item['rename_columns']
                )
            )

    def clean(self):
        dataset_merged = []
        for dataset in self.datasets:
            dataset.clean()
            dataset_merged.append(dataset.df)
            print(dataset.df)
        self.final_dataset = pd.concat(
            dataset_merged).drop_duplicates(subset=[self.config['main_column']])

    def add_gender(self):
        self.final_dataset['gender'] = self.final_dataset['name'].apply(
            lambda x: get_gender(x.split(" ")[0]))

    def save(self):
        self.final_dataset.to_json(
            self.config['output_file'], orient='records', indent=4)
        return


if __name__ == "__main__":
    datasets = DataIterator(CONFIG_PATH)
    datasets.iterate()
    datasets.clean()
    datasets.add_gender()
    datasets.save()
