"""Read-only explanation of persisted scoped FACT. No financial calculations."""
from .gap_preparation import saved_preview


def context(record, facts):
    prefix=f"gap.v1.{record['preparation_id']}."
    scoped={key:value for key,value in facts.items() if key.startswith(prefix)}
    usable={key:value for key,value in scoped.items() if value.get('status')=='KNOWN'}
    unresolved={key:value for key,value in scoped.items() if value.get('status') in ('UNKNOWN','STALE')}
    preview=saved_preview(record)
    return {'mode':'DETERMINISTIC_FACT_EXPLANATION','preparation_id':record['preparation_id'],
            'revision':record.get('revision',0),'known_facts':usable,'unresolved_facts':unresolved,
            'findings':preview['findings'],'next_actions':preview['top3'],
            'explanation':f"저장된 정보 중 확인한 항목은 {len(usable)}개, 미확인·재검토 항목은 {len(unresolved)}개입니다. 다음 행동은 확인 상태에 따라 정했습니다.",
            'precision_connection':{'status':'CANONICAL_MAPPING_REQUIRED','automatic_import':False,
              'reason':'월 시점과 만원 단위 정보를 기존 나이·원 단위 입력으로 임의 변환하지 않습니다.'},
            'limitations':['자기확인 정보이며 기관 검증이 아닙니다.','부분 확인은 완료가 아닙니다.','계획 소득을 확정 수입으로 합산하지 않습니다.','월 부족액·필요자금·자산 소진 나이를 새로 계산하지 않습니다.'],
            'fact_writes':False}
