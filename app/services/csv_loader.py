import csv
from pathlib import Path
from typing import List, Dict, Optional


class CSVLoaderService:
    """Service to load and filter CLO/PLO data from CSV files."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
    
    def load_clos(
        self, 
        curriculum_id: Optional[int] = None, 
        course_id: Optional[int] = None
    ) -> List[Dict]:
        """Load CLOs from tlic_obe_public_clo.csv with optional filtering."""
        clo_file = self.data_dir / "tlic_obe_public_clo.csv"
        
        clos = []
        with open(clo_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by course_id if provided
                if course_id is not None:
                    row_course_id = row.get('course_id', '').strip()
                    if row_course_id and int(row_course_id) != course_id:
                        continue
                
                # Skip deleted entries
                if row.get('deleted_at', '').strip():
                    continue
                
                clos.append({
                    'id': row.get('id', '').strip(),
                    'course_id': row.get('course_id', '').strip(),
                    'no': row.get('no', '').strip(),
                    'description': row.get('description', '').strip(),
                    'category': row.get('category', '').strip(),
                })
        
        return clos
    
    def load_all_clos(self) -> List[Dict]:
        """Load ALL CLOs from tlic_obe_public_clo.csv without any filtering."""
        clo_file = self.data_dir / "tlic_obe_public_clo.csv"
        mapping_file = self.data_dir / "tlic_obe_public_clo_has_plos.csv"
        
        # Build a map of course_id -> curriculum_id from the mapping file
        course_to_curriculum = {}
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course_id = row.get('course_id', '').strip()
                curriculum_id = row.get('curriculum_id', '').strip()
                if course_id and curriculum_id:
                    course_to_curriculum[course_id] = curriculum_id
        
        clos = []
        seen_clos = set()  # Track unique (curriculum_id, course_id, clo_id) combinations
        
        with open(clo_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip deleted entries
                if row.get('deleted_at', '').strip():
                    continue
                
                clo_id = row.get('id', '').strip()
                course_id = row.get('course_id', '').strip()
                # Get curriculum_id from the mapping
                curriculum_id = course_to_curriculum.get(course_id, '')
                
                # Create unique key for deduplication
                clo_key = (curriculum_id, course_id, clo_id)
                
                # Skip if we've already seen this combination
                if clo_key in seen_clos:
                    continue
                
                seen_clos.add(clo_key)
                
                clos.append({
                    'id': clo_id,
                    'course_id': course_id,
                    'curriculum_id': curriculum_id,
                    'no': row.get('no', '').strip(),
                    'description': row.get('description', '').strip(),
                    'category': row.get('category', '').strip(),
                })
        
        return clos
    
    def load_clo_plo_mappings(
        self,
        curriculum_id: Optional[int] = None,
        course_id: Optional[int] = None,
        clo_ids: Optional[List[str]] = None,
        is_map_only: bool = True
    ) -> List[Dict]:
        """Load CLO-PLO mappings from tlic_obe_public_clo_has_plos.csv."""
        mapping_file = self.data_dir / "tlic_obe_public_clo_has_plos.csv"
        
        mappings = []
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by is_map
                if is_map_only:
                    is_map = row.get('is_map', '').strip().lower()
                    if is_map != 'true':
                        continue
                
                # Filter by curriculum_id if provided
                if curriculum_id is not None:
                    row_curriculum_id = row.get('curriculum_id', '').strip()
                    if row_curriculum_id and int(row_curriculum_id) != curriculum_id:
                        continue
                
                # Filter by course_id if provided
                if course_id is not None:
                    row_course_id = row.get('course_id', '').strip()
                    if row_course_id and int(row_course_id) != course_id:
                        continue
                
                # Filter by clo_ids if provided
                if clo_ids is not None:
                    row_clo_id = row.get('clo_id', '').strip()
                    if row_clo_id not in clo_ids:
                        continue
                
                mappings.append({
                    'id': row.get('id', '').strip(),
                    'curriculum_id': row.get('curriculum_id', '').strip(),
                    'course_id': row.get('course_id', '').strip(),
                    'clo_id': row.get('clo_id', '').strip(),
                    'plo_id': row.get('plo_id', '').strip(),
                    'is_map': row.get('is_map', '').strip(),
                })
        
        return mappings
    
    def load_plos(
        self,
        curriculum_id: Optional[int] = None,
        plo_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Load PLOs from tlic_obe_public_plo.csv."""
        plo_file = self.data_dir / "tlic_obe_public_plo.csv"
        
        plos = []
        with open(plo_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by curriculum_id if provided
                if curriculum_id is not None:
                    row_curriculum_id = row.get('curriculum_id', '').strip()
                    if row_curriculum_id and int(row_curriculum_id) != curriculum_id:
                        continue
                
                # Filter by plo_ids if provided
                if plo_ids is not None:
                    row_id = row.get('id', '').strip()
                    if row_id not in plo_ids:
                        continue
                
                # Skip deleted entries
                if row.get('deleted_at', '').strip():
                    continue
                
                plos.append({
                    'id': row.get('id', '').strip(),
                    'curriculum_id': row.get('curriculum_id', '').strip(),
                    'name': row.get('name', '').strip(),
                    'name_en': row.get('name_en', '').strip(),
                    'detail': row.get('detail', '').strip(),
                    'plo_level': row.get('plo_level', '').strip(),
                    'parent_plo_id': row.get('parent_plo_id', '').strip(),
                })
        
        return plos
    
    def get_plos_for_clos(
        self,
        clo_ids: List[str],
        curriculum_id: int,
        course_id: int
    ) -> List[Dict]:
        """Get all PLOs mapped to the given CLO IDs."""
        # Get mappings
        mappings = self.load_clo_plo_mappings(
            curriculum_id=curriculum_id,
            course_id=course_id,
            clo_ids=clo_ids,
            is_map_only=True
        )
        
        # Extract unique PLO IDs
        plo_ids = list(set([m['plo_id'] for m in mappings if m['plo_id']]))
        
        if not plo_ids:
            return []
        
        # Load PLO details
        plos = self.load_plos(curriculum_id=curriculum_id, plo_ids=plo_ids)
        
        return plos
    
    def get_plos_for_clo_contexts(
        self,
        clo_contexts: List[Dict]
    ) -> List[Dict]:
        """Get all PLOs mapped to CLOs with their curriculum_id and course_id context.
        
        Args:
            clo_contexts: List of dicts with 'clo_id', 'curriculum_id', 'course_id'
        
        Returns:
            List of PLO dictionaries
        """
        all_plos = []
        seen_plo_ids = set()
        
        # Group by curriculum_id and course_id for efficient querying
        from collections import defaultdict
        grouped = defaultdict(list)
        for ctx in clo_contexts:
            key = (ctx['curriculum_id'], ctx['course_id'])
            grouped[key].append(ctx['clo_id'])
        
        # Query PLOs for each group
        for (curriculum_id, course_id), clo_ids in grouped.items():
            plos = self.get_plos_for_clos(
                clo_ids=clo_ids,
                curriculum_id=curriculum_id,
                course_id=course_id
            )
            
            # Add unique PLOs
            for plo in plos:
                plo_key = (plo['id'], plo['curriculum_id'])
                if plo_key not in seen_plo_ids:
                    seen_plo_ids.add(plo_key)
                    all_plos.append(plo)
        
        return all_plos
