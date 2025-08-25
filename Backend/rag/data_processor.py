import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai
from langchain.schema import Document
from typing import List, Dict, Optional, Any
import logging
import json
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchoolDataProcessor:
    """
    Enhanced processor for school data with year-wise indexing and optimal chunking
    """
    
    def __init__(self, excel_file_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.excel_file_path = excel_file_path
        self.model_name = model_name
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        
        # Optimal chunking parameters based on data size
        self.chunk_size = 500  # Increased for better context
        self.chunk_overlap = 100  # Add overlap for better continuity
        
    def load_and_clean_excel_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load Excel file and clean data from all sheets
        """
        try:
            # Read all sheets
            excel_data = pd.read_excel(self.excel_file_path, sheet_name=None)
            
            cleaned_data = {}
            sheet_year_mapping = {
                0: "2022",  # First sheet
                1: "2023",  # Second sheet  
                2: "2024",  # Third sheet
                3: "2025"   # Fourth sheet
            }
            
            for idx, (sheet_name, df) in enumerate(list(excel_data.items())[:-1]):
                year = sheet_year_mapping.get(idx, f"Sheet_{idx}")
                
                # Clean the dataframe
                df_cleaned = self.clean_dataframe(df, year)
                cleaned_data[year] = df_cleaned
                
                logger.info(f"Loaded {year} data: {len(df_cleaned)} rows")
                
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def clean_dataframe(self, df: pd.DataFrame, year: str) -> pd.DataFrame:
        """
        Clean individual dataframe with proper column handling
        """
        # Ensure we have exactly 2 columns
        if len(df.columns) < 2:
            raise ValueError(f"Sheet for {year} must have at least 2 columns")
        
        # Take first two columns and rename them
        df_clean = df.iloc[:, :2].copy()
        df_clean.columns = ['country', 'school_name']
        
        # Clean data
        df_clean['country'] = df_clean['country'].astype(str).str.strip()
        df_clean['school_name'] = df_clean['school_name'].astype(str).str.strip()
        
        # Special handling for 2022 "merged cell style"
        if str(year) == "2022":
            df_clean['country'] = df_clean['country'].replace(['', 'nan', None], pd.NA)
            df_clean['country'] = df_clean['country'].ffill()   # forward fill country names
        
        # Remove empty rows
        df_clean = df_clean.dropna(subset=['country', 'school_name'])
        df_clean = df_clean[df_clean['country'] != '']
        df_clean = df_clean[df_clean['school_name'] != '']
        df_clean = df_clean[df_clean['country'] != 'nan']
        df_clean = df_clean[df_clean['school_name'] != 'nan']
        
        # Add year column
        df_clean['year'] = year
        
        return df_clean
    
    def create_structured_documents(self, data_dict: Dict[str, pd.DataFrame]) -> List[Document]:
        """
        Create structured documents optimized for retrieval
        """
        documents = []
        
        for year, df in data_dict.items():
            # Group by country for better organization
            country_groups = df.groupby('country')
            
            for country, group in country_groups:
                schools = group['school_name'].tolist()
                
                # Create multiple document formats for better retrieval
                
                # 1. Country-Year summary document
                school_list = ", ".join(schools[:10])  # First 10 schools
                if len(schools) > 10:
                    school_list += f" and {len(schools) - 10} more schools"
                
                summary_content = (
                    f"In {year}, {country} had {len(schools)} schools including: {school_list}."
                )
                
                summary_doc = Document(
                    page_content=summary_content,
                    metadata={
                        "year": year,
                        "country": country,
                        "school_count": len(schools),
                        "document_type": "country_summary"
                    }
                )
                documents.append(summary_doc)
                
                # 2. Detailed school listings (chunked if too many schools)
                if len(schools) <= 15:
                    # Small lists - single document
                    school_content = (
                        f"Schools in {country} ({year}): " + "; ".join(schools)
                    )
                    school_doc = Document(
                        page_content=school_content,
                        metadata={
                            "year": year,
                            "country": country,
                            "school_count": len(schools),
                            "document_type": "school_list"
                        }
                    )
                    documents.append(school_doc)
                else:
                    # Large lists - create chunks
                    chunk_size = 15
                    for i in range(0, len(schools), chunk_size):
                        chunk_schools = schools[i:i + chunk_size]
                        chunk_content = (
                            f"Schools in {country} ({year}) - Part {i//chunk_size + 1}: " + 
                            "; ".join(chunk_schools)
                        )
                        chunk_doc = Document(
                            page_content=chunk_content,
                            metadata={
                                "year": year,
                                "country": country,
                                "chunk_id": i//chunk_size + 1,
                                "total_schools_in_country": len(schools),
                                "document_type": "school_list_chunk"
                            }
                        )
                        documents.append(chunk_doc)
                
                # 3. Individual school documents for exact matches
                for school in schools:
                    individual_content = f"{school} is a school located in {country} (data from {year})"
                    individual_doc = Document(
                        page_content=individual_content,
                        metadata={
                            "year": year,
                            "country": country,
                            "school_name": school,
                            "document_type": "individual_school"
                        }
                    )
                    documents.append(individual_doc)
        
        logger.info(f"Created {len(documents)} documents for indexing")
        return documents
    
    def create_year_wise_index(self, documents: List[Document]) -> FAISS:
        """
        Create FAISS index with year-wise optimization
        """
        if not documents:
            raise ValueError("No documents to index")
        
        # Use RecursiveCharacterTextSplitter for optimal chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "; ", ", ", " ", ""]  # Better separators for your data
        )
        
        # Split documents
        split_docs = text_splitter.split_documents(documents)
        
        logger.info(f"Split into {len(split_docs)} chunks for indexing")
        
        # Create FAISS index
        db = FAISS.from_documents(split_docs, self.embeddings)
        
        return db
    
    def build_faiss_index(self) -> FAISS:
        """
        Main method to build FAISS index from Excel data
        """
        try:
            # Load and clean data
            logger.info("Loading Excel data...")
            data_dict = self.load_and_clean_excel_data()
            
            # Print data_dict info
            print("\n=== CLEANED DATA DICT ===")
            print(f"Total years: {len(data_dict)}")
            for year, df in data_dict.items():
                print(f"\n{year} Data:")
                print(f"Length: {len(df)} rows")
                print("First 20 rows:")
                print(df.head(20).to_string())
                
            
            # Create structured documents
            logger.info("Creating structured documents...")
            documents = self.create_structured_documents(data_dict)
            
            # Print documents info
            print("\n=== STRUCTURED DOCUMENTS ===")
            print(f"Total documents: {len(documents)}")
            print("\nFirst 20 documents:")
            for i, doc in enumerate(documents[:20]):
                print(f"\nDoc {i+1}:")
                print(f"Content: {doc.page_content}")
                print(f"Metadata: {doc.metadata}")
            
            
            # Build FAISS index
            logger.info("Building FAISS index...")
            db = self.create_year_wise_index(documents)
            
            # Print final FAISS info
            print(f"\n=== FAISS INDEX ===")
            print(f"Total vectors in index: {db.index.ntotal}")
            
            
            logger.info("FAISS index built successfully!")
            return db
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}")
            raise
        
        
genai.configure(api_key="AIzaSyANj4bwTAp1cCRf6m5xiZGlVfxZtZx365Q")        
        
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash"
)

def extract_query_entities(query: str) -> Dict[str, Optional[str]]:
    """
    Uses Gemini to extract 'country', 'year', and 'school_name' from a query.
    Always returns a dict with keys even if None.
    """
    prompt = f"""
    Extract the following entities from the user query strictly in JSON format:
    - country (if present)
    - year (only 2022–2025 if present)
    - school_name (if present)

    Also make sure if country in query is United States, you should add it as: "USA"

    Query: "{query}"

    Output only JSON strictly in this format:
    {{
      "country": "<country or null>",
      "year": "<year or null>",
      "school_name": "<school name or null>"
    }}
    """

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 200,
            "top_p": 0.8,
            "top_k": 40
        }
    )

    try:
        text = response.text.strip()

        # Step 2: Extract JSON substring using regex (handles cases with extra text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        # Step 3: Try loading JSON
        result = json.loads(text)
        
        # Parse JSON safely
        # result = json.loads(response.text)
        
        print("Model's result: ", result)
        
    except Exception:
        # Fallback if Gemini returns something unexpected
        result = {"country": None, "year": None, "school_name": None}
    
    return result


# def get_retriever_for_query(query: str, k: int = 10):
#     """Return a retriever that enforces year filtering if a year is present."""
#     year = _extract_year(query)
#     kwargs = {"k": k, "fetch_k": max(50, k * 5)}
#     if year:
#         kwargs["filter"] = {"year": year}  # <- metadata filter
#     # search_type may vary by LC version; both forms are fine
#     return db.as_retriever(search_type="similarity", search_kwargs=kwargs)


def retrieve(db, query: str, k: int = 10) -> List[Document]:
    """Convenience: run the retrieval with entity-based filtering + graceful fallback."""
    # entities = extract_query_entities(query)  # {"year": ..., "country": ..., "school": ...}

    # kwargs = {"k": k, "fetch_k": max(50, k * 5)}

    # print("Model's entities: ", entities)

    # # Build filter dict dynamically from available entities
    # filter_kwargs = {}
    # if entities.get("year"):
    #     filter_kwargs["year"] = entities["year"]
    # if entities.get("country"):
    #     filter_kwargs["country"] = entities["country"]
    # if entities.get("school_name"):
    #     filter_kwargs["school_name"] = entities["school_name"]

    # if filter_kwargs:
    #     kwargs["filter"] = filter_kwargs

    # # primary: filtered search
    # docs = db.as_retriever(search_type="similarity", search_kwargs=kwargs) \
    #             .get_relevant_documents(query)

    # # fallback: if nothing found with filter, drop the filter
    # if not docs and filter_kwargs:
    #     docs = db.as_retriever(search_type="similarity",
    #                            search_kwargs={"k": k, "fetch_k": max(50, k * 5)}) \
    #                 .get_relevant_documents(query)
    
    prompt = f"""
        Extract the following entities from the user query strictly in JSON format:
        - country (if present)
        - year (only 2022–2025 if present)

        Also make sure if country in query is United States, you should add it as: "USA"

        Query: "{query}"

        Output only JSON strictly in this format:
        {{
        "country": "<country or null>",
        "year": "<year or null>"
        }}
        """

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 200,
            "top_p": 0.8,
            "top_k": 40
        }
    )

    try:
        text = response.text.strip()

        # Step 2: Extract JSON substring using regex (handles cases with extra text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        # Step 3: Try loading JSON
        entities = json.loads(text)
        
        print("Model's result: ", entities)
        
    except Exception:
        # Fallback if Gemini returns something unexpected
        entities = {"country": None, "year": None}
        
    k = 10
        
    kwargs = {"k": k, "fetch_k": max(50, k * 5)}

    print("Model's entities: ", entities)

    # Build filter dict dynamically from available entities
    filter_kwargs = {}
    
    filter_kwargs["year"] = "2024"  # Hardcoded to 2024 for count retrieval
    
    if entities.get("country"):
        filter_kwargs["country"] = entities["country"]
        
    # filter_kwargs["total_schools_in_country"] = "total_schools_in_country"
    # filter_kwargs["school_count"] = "school_count"
        
    if filter_kwargs:
        kwargs["filter"] = filter_kwargs

    print("")
    print("--------------------------------Kwargs:", kwargs)
    print("")

    # primary: filtered search
    retriever = db.as_retriever(search_type="similarity", search_kwargs=kwargs)

    docs = retriever.get_relevant_documents(query)

    # fallback: if nothing found with filter, drop the filter
    if not docs and filter_kwargs:
        retriever = db.as_retriever(search_type="similarity",
                            search_kwargs={"k": k, "fetch_k": max(50, k * 5)})
    
    return retriever.get_relevant_documents(query)
    

# Updated method for your StoryCreativityChain class
def build_faiss_index(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """
    Enhanced build_faiss_index method to replace in your StoryCreativityChain class
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for Excel file in the current directory or parent directory
    excel_file_path = None
    name = "TEP 2022, 2023, 2024, 2025 Schools .xlsx" 
    
    # Check current directory first
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(current_dir, name)

    if not excel_file_path:
        raise FileNotFoundError(
            f"Excel file not found. Please place your Excel file in {current_dir} "
            f"with this name: {', '.join(name)}"
        )
    
    print(f"Using Excel file: {excel_file_path}")
    
    # Use the enhanced processor
    processor = SchoolDataProcessor(excel_file_path, model_name)
    db = processor.build_faiss_index()
    
    return db


# Example usage and testing function
def test_retrieval(db: FAISS, test_queries: List[str]):
    """
    Test function to verify retrieval quality
    """
    # retriever = db.as_retriever(search_kwargs={"k": 5})
    
    print("\n=== Testing Retrieval ===")
    for query in test_queries:
        print(f"\nQuery: {query}")
        docs = retrieve(db, query)
        for i, doc in enumerate(docs):  # Show top 3 results
            print(f"  Result {i+1}: {doc.page_content}")
            print(f"  Metadata: {doc.metadata}")


# Test queries for your use case
TEST_QUERIES = [
    # "Which schools were in Pakistan in year 2024",
    # "schools in USA in year 2022",
    # "year 2023 schools data",
    # "educational institutions in Canada in 2022",
    # "recent school data of year 2025"
    "Pakistan"
]


# Main function to run everything
def main():
    """
    Main function to process Excel data and build FAISS index
    """
    try:
        # Excel file path
        # name = "TEP 2022, 2023, 2024, 2025 Schools .xlsx"   
        
        # excel_file_path = None
        
        # # Check current directory first
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # excel_file_path = os.path.join(current_dir, name)
        
        # # Initialize processor
        # processor = SchoolDataProcessor(excel_file_path)
        
        # # Build FAISS index
        # db = processor.build_faiss_index()
        
        # # Save index
        # db.save_local("faiss_index")
        # print("FAISS index saved successfully!")
        
        
        name = "faiss_index"
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        faiss_path = os.path.join(current_dir, name)
        
        print("Loading FAISS index from disk...")
        db = FAISS.load_local(faiss_path, HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"), allow_dangerous_deserialization=True)
        
        # Optional: Test retrieval
        test_retrieval(db, TEST_QUERIES)
        
        return db
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# Run the main function
if __name__ == "__main__":
    db = main()
