// Neo4j 인덱스 마이그레이션 스크립트 테스트용 샘플 데이터
// 노드, 관계, 태그, 중복, 누락 등 다양한 케이스 포함

// 노드 생성
CREATE (:DataNode {id: 'node-1', name: 'Alpha', tags: ['tagA', 'tagB'], created_at: datetime(), ref_count: 1});
CREATE (:DataNode {id: 'node-2', name: 'Beta', tags: ['tagB'], created_at: datetime(), ref_count: 0});
CREATE (:DataNode {id: 'node-3', name: 'Gamma', tags: [], created_at: datetime(), ref_count: 2});
CREATE (:DataNode {id: 'node-4', name: 'Delta', ref_count: 0}); // tags, created_at 누락

// 관계 생성 (MATCH로 노드 id 기준 연결)
MATCH (n1:DataNode {id: 'node-1'}), (n2:DataNode {id: 'node-2'}) CREATE (n1)-[:DEPENDS_ON]->(n2);
MATCH (n2:DataNode {id: 'node-2'}), (n3:DataNode {id: 'node-3'}) CREATE (n2)-[:DEPENDS_ON]->(n3);
MATCH (n3:DataNode {id: 'node-3'}), (n4:DataNode {id: 'node-4'}) CREATE (n3)-[:DEPENDS_ON]->(n4);

// 중복 노드 (id 중복)
CREATE (:DataNode {id: 'node-1', name: 'AlphaDup', tags: ['tagA'], created_at: datetime(), ref_count: 0});

// 태그 기반 노드
CREATE (:DataNode {id: 'node-5', name: 'Tagged', tags: ['tagC', 'tagD'], created_at: datetime(), ref_count: 1});

// 인덱스 없는 노드
CREATE (:OtherNode {foo: 'bar'});
