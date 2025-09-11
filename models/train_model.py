# #11111111111111111111111111111111111

# #train_model.py
# import pandas as pd
# import joblib
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import classification_report, accuracy_score

# # Load dataset
# df = pd.read_csv("sign_data.csv")

# # Rename last column as "target" (it holds your labels like A, B, C...)
# df.columns = list(df.columns[:-1]) + ["target"]

# # Split features (X) and labels (y)
# X = df.drop("target", axis=1)
# y = df["target"]

# # Encode labels
# label_encoder = LabelEncoder()
# y_encoded = label_encoder.fit_transform(y)

# # Train-test split
# X_train, X_test, y_train, y_test = train_test_split(
#     X, y_encoded, test_size=0.2, random_state=42
# )

# # Train Random Forest
# model = RandomForestClassifier(n_estimators=200, random_state=42)
# model.fit(X_train, y_train)

# # Evaluate
# y_pred = model.predict(X_test)
# print("✅ Accuracy:", accuracy_score(y_test, y_pred))
# print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# # Save model and encoder
# joblib.dump(model, "sign_model.pkl")
# joblib.dump(label_encoder, "label_encoder.pkl")

# print("🎉 Model and label encoder saved successfully!")



#22222222222222222 WORD + LETTERS
# train_model.py
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import LabelEncoder
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import classification_report, confusion_matrix
# import joblib
# from collections import Counter
# import os

# # CONFIG
# DATA_CSV = "sign_data.csv"
# MODEL_FILE = "sign_model.pkl"
# ENCODER_FILE = "label_encoder.pkl"

# if not os.path.exists(DATA_CSV):
#     raise FileNotFoundError(f"{DATA_CSV} not found. Run data_collect.py first.")

# print("📂 Loading dataset...")
# df = pd.read_csv(DATA_CSV)

# # Determine label column (last column if not present)
# if "label" in df.columns:
#     label_col = "label"
# elif "target" in df.columns:
#     label_col = "target"
# else:
#     label_col = df.columns[-1]  # fallback to last column
#     # rename to 'label' for clarity
#     if label_col != "label":
#         df = df.rename(columns={label_col: "label"})
#         label_col = "label"

# # Ensure feature cols are numeric
# feature_cols = [c for c in df.columns if c != label_col]
# df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors='coerce')

# # drop rows with NaNs if any
# before = len(df)
# df = df.dropna().reset_index(drop=True)
# after = len(df)
# print(f"Rows before cleaning: {before}, after dropping NaNs: {after}")

# X = df[feature_cols].values
# y = df[label_col].values.astype(str)

# # encode labels
# le = LabelEncoder()
# y_enc = le.fit_transform(y)

# # class distribution
# counts = Counter(y)
# print("\n🔎 Class distribution (sample counts):")
# for k, v in counts.items():
#     print(f"{k:12} -> {v}")

# # train/test split (stratified)
# X_train, X_test, y_train, y_test = train_test_split(
#     X, y_enc, test_size=0.2, stratify=y_enc, random_state=42
# )

# print("\n🌲 Training RandomForest with class_weight='balanced'...")
# clf = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=42, n_jobs=-1)
# clf.fit(X_train, y_train)

# # evaluate
# y_pred = clf.predict(X_test)
# print("\n📊 Classification Report:")
# print(classification_report(y_test, y_pred, target_names=le.classes_))
# print("\n📉 Confusion Matrix (rows=true, cols=pred):")
# print(confusion_matrix(y_test, y_pred))

# # save
# joblib.dump(clf, MODEL_FILE)
# joblib.dump(le, ENCODER_FILE)
# print(f"\n✅ Model saved to {MODEL_FILE}")
# print(f"✅ Label encoder saved to {ENCODER_FILE}")


#333333333333333333333333333333333333 TRYING AGAIN
# train_model.py
# train_model.py
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

print("📂 Loading dataset...")

# Load dataset
df = pd.read_csv("sign_data.csv")

print(f"Rows before cleaning: {len(df)}, after dropping NaNs: {len(df.dropna())}")
df = df.dropna()

# Force last column to be 'label'
df.columns = [f"f{i}" for i in range(df.shape[1] - 1)] + ["label"]

print("\n📝 Dataset columns:", df.columns.tolist())

# Separate features (X) and labels (y)
X = df.drop("label", axis=1).values
y = df["label"].values

# Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Show class distribution
print("\n🔎 Class distribution (sample counts):")
for cls, count in df["label"].value_counts().items():
    print(f"{cls:<12} -> {count}")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42
)

print("\n🌲 Training RandomForest with class_weight='balanced'...")
clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

print("\n📉 Confusion Matrix (rows=true, cols=pred):")
cm = confusion_matrix(y_test, y_pred)
print(cm)

# Plot confusion matrix
plt.figure(figsize=(12, 10))
plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.colorbar()

tick_marks = np.arange(len(label_encoder.classes_))
plt.xticks(tick_marks, label_encoder.classes_, rotation=90)
plt.yticks(tick_marks, label_encoder.classes_)

plt.ylabel("True label")
plt.xlabel("Predicted label")

# Overlay numbers on matrix
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, str(cm[i, j]),
                 ha="center", va="center",
                 color="white" if cm[i, j] > cm.max() / 2 else "black")

plt.tight_layout()
plt.show()

# Save model + encoder
joblib.dump(clf, "sign_model.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
print("\n✅ Model saved to sign_model.pkl")
print("✅ Label encoder saved to label_encoder.pkl")







