"""
copy this into colab notebook to train on gpu. model is saved to models folder.
"""
!pip install rasa==2.8.11 spacy transformers --use-deprecated=legacy-resolver
%cd /content/drive/MyDrive/colab
!cp -r .ssh ~
!rm -rf chatbot
!git clone git@github.com:simonm3/chatbot.git
!pip uninstall urllib3 -y
!pip install -U urllib3
!python -m spacy download en_core_web_md
%cd chatbot
!rasa train