# There will be news

The [GPT-2](https://openai.com/blog/better-language-models/) model released by [huggingface](https://github.com/huggingface/pytorch-transformers), as part of the set of pre-trained models available on [Pytorch Hub](https://pytorch.org/hub/huggingface_pytorch-transformers/), has been fine tuned using a [dataset of news](https://www.kaggle.com/rmisra/news-category-dataset) extracted from [Huffpost web](https://www.huffpost.com/).

The main goal of this project is to explore how models can output texts resembling the structure and style of news from a traditional newspaper. For that purpose, [we've developed a simple web](https://therewillbenews.thesupertoys.org/) showing the latest news created by the trained model.   

The model (1,4 GB) is not hosted in this repository as it would exceed the max limit allowed by Github. But the file `training_medium_news.ipynb` it's the Jupyter Notebook that we used for training the model, you can either use that script to train it yourself or download it from this [Google Drive shared URL](https://drive.google.com/file/d/17JVZL8KJZYBQGOIgyqs9u_X_vdFKr58J/view?usp=sharing).  