# Language-data sources

The attack code is self-contained: no network request is made at runtime.

- `english_corpus.txt`: 600,000 normalized A–Z letters used only to train the character-quadgram scorer. Equal 300,000-letter samples come from:
  - *Pride and Prejudice*, Jane Austen, Project Gutenberg eBook 1342: https://www.gutenberg.org/ebooks/1342
  - *The Adventures of Sherlock Holmes*, Arthur Conan Doyle, Project Gutenberg eBook 1661: https://www.gutenberg.org/ebooks/1661
- `evaluation_corpus.txt`: 585,537 normalized A–Z letters from a different work, used to generate test messages:
  - *A Tale of Two Cities*, Charles Dickens, Project Gutenberg eBook 98: https://www.gutenberg.org/ebooks/98

These Project Gutenberg texts are public-domain source texts in the United States. Project Gutenberg header/footer material was removed before normalization. Training and evaluation sources are deliberately separate to reduce corpus leakage.
