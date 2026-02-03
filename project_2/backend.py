import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os


class MedicineRecommender:
    def __init__(self):
        dd = "demo6.csv"
        if not os.path.exists(dd):
            print("{dd} file missing")
            exit()

        # read dataset
        self.df = pd.read_csv("demo6.csv")
        print("Dataset loaded successfully")

        # clean and normalize
        self.df['Symptom'] = self.df['Symptom'].str.lower()
        self.df['Medicine'] = self.df['Medicine'].str.lower()

        # handle multiple symptoms if comma-separated
        self.df['Symptoms_list'] = self.df['Symptom'].apply(
            lambda x: [i.strip() for i in x.split(',')]
        )

        # encoders
        self.med_enc = LabelEncoder()
        self.df['med_label'] = self.med_enc.fit_transform(self.df['Medicine'])

        self.age_enc = LabelEncoder()
        self.df['age_label'] = self.age_enc.fit_transform(self.df['Age Group'])

        self.sym_bin = MultiLabelBinarizer()
        sym_matrix = self.sym_bin.fit_transform(self.df['Symptoms_list'])

        X = np.hstack((sym_matrix, self.df['age_label'].values.reshape(-1, 1)))
        y = self.df['med_label']

        # train-test split
        x_train, x_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # models
        self.nb = GaussianNB()
        self.rf = RandomForestClassifier()
        self.knn = KNeighborsClassifier()

        self.nb.fit(x_train, y_train)
        self.rf.fit(x_train, y_train)
        self.knn.fit(x_train, y_train)

        p1 = self.nb.predict(x_test)
        p2 = self.rf.predict(x_test)
        p3 = self.knn.predict(x_test)

        print("Naive Bayes acc:", round(accuracy_score(y_test, p1), 2))
        print("Random Forest acc:", round(accuracy_score(y_test, p2), 2))
        print("KNN acc:", round(accuracy_score(y_test, p3), 2))

    def age_grp(self, age):
        if age <= 1:
            return "Below 1 year"
        elif 1 < age <= 3:
            return "1-3 years"
        elif 4 <= age <= 6:
            return "3-6 years"
        elif 7 <= age <= 15:
            return "6-15 years"
        else:
            return "Above 15 years"

    def dur_to_days(self, d):
        d = d.lower().strip()
        days = 0
        if "day" in d:
            try:
                days = int(d.split()[0])
            except:
                days = 0
        elif "week" in d:
            try:
                w = int(d.split()[0])
                days = w * 7
            except:
                days = 7
        return days

    def recommend(self, sym_input, age, gender, preg, feed, dur):
        age_grp = self.age_grp(age)  # categorical value
        dur_days = self.dur_to_days(dur)  # integer value

        if dur_days > 9:
            return "If you’ve been feeling unwell for more than a week, it means your symptom is getting worse.\nIt’s important to consult a doctor so you can find out what’s wrong and get the right treatment.\n sorry I cannot help you with that."

        symptoms = [i.strip().lower() for i in sym_input.split(',')]
        results = []

        for s in symptoms:
            # direct lookup
            match = self.df[
                (self.df['Symptom'].str.contains(s, case=False, na=False)) &
                (self.df['Age Group'].str.lower() == age_grp.lower())
            ]

            if len(match) > 0:
                results.append(f"\nFor symptom '{s}':")
                for k, row in match.iterrows():
                    med = row['Medicine']
                    dose = row['Dosage'] if 'Dosage' in self.df.columns else 'N/A'
                    results.append(
                        f"  -> Medicine: {med} \n  -> Dosage: {dose}")
            else:
                # ML fallback if no match found
                try:
                    sym_vec = self.sym_bin.transform([[s]])
                    age_vec = self.age_enc.transform([age_grp]).reshape(-1, 1)
                    x_in = np.hstack((sym_vec, age_vec))
                    preds = [
                        self.nb.predict(x_in)[0],
                        self.rf.predict(x_in)[0],
                        self.knn.predict(x_in)[0]
                    ]
                    final_pred = max(set(preds), key=preds.count)
                    model_med = self.med_enc.inverse_transform([final_pred])[0]
                    results.append(f"\nFor symptom '{s}':")
                    results.append(f"   Predicted (ML Model): {model_med}")
                except Exception as e:
                    results.append(
                        f"\nFor symptom '{s}': Error in model prediction")

        if gender.lower() == "female" and age >= 18:
            if preg.lower() == "yes":
                results.append(
                    "\nNote: You are pregnant. Please Consult a doctor before taking the medicine.")
            if feed.lower() == "yes":
                results.append(
                    "\nNote: You are feeding a baby.Please Consult a doctor before taking the medicine.")

        return "\n".join(results)
