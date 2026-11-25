from langchain_text_splitters import TokenTextSplitter


def create_chunks(text):

    splitter = TokenTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )

    return splitter.split_text(text)