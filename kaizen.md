# Kaizen9�	_� (���

## ��

SnKaizen_�o#�����kqU�_9��H�����gY� �4gn���9�;Ւ/�W���j9��������W~Y

## _���

### 1. 9��Hn\��
- 9��Hn{2��Jd
- �������H--��-��t	
- *H�-��-N	
- #;hn�#�Q

### 2. �������_�
- #;n���h:
- �%������
- CSVա��k�� ����{2
- �뿤�gn2W����

### 3. CSV ��������
- #;���n �{2
- �������n��
- ��������h<_�

## (��

### �������;bgnCSV������

1. **������**
   - #����� � �������
   - URL: `/production/gantt_chart/`

2. **CSVա��b**
   ```csv
   QR���,��No,��No,�H,�4,����,� ���,�w���,�,�,p�,���Ȉ��,��Ȉ��,�������,V������󰈚�,��刚�,����,��؈��,�����؈��
   24112050,24112,205,*>ƹ�,q��ƹ�:,-16*19*P���,2025/05/18 0:00,2025/05/19 0:00,�P (�),����,49,2025/05/14 0:00,2025/05/15 0:00,,2025/06/27 0:00,,,2025/08/03 0:00,
   ```

3. **������K**
   - CSVա�������gա��x�
   - ������ܿ��ï
   - �P����

### 9��Hn�

1. **9��Hn\**
   - #����� � 9��H
   - URL: `/production/kaizen/`

2. **9��Hn�**
   - ����: 9��Hn��
   - �: s0j9���
   - �##;: �ahj�#;
   - �#�: �ahj��
   - *H�: 9�n�%�
   - ���: 9�k����n�,
   - ��n��: �Ōn��,�

3. **������**
   - �H-: 9��HL��U�_�K
   - -: 9��H�WfD��K
   - ��-: 9�V���WfD��K
   - ��: 9�L��W_�K
   - t: 9��HLtU�_�K

## ������� 

### ProductionPlan#;	
- �,�1: ;�����p��
- CSV��գ���: QR�����No��No�H�4I
- ����: �n���Bգ���

### ProcessSchedule�������	
- #;hn�#�Q
- �h�������1
- 2W������

### Kaizen9��H	
- �H�1: ������H
- �#�1: #;�hn�#�Q
- ��1: �����*H���,�

## rQh:

�������go�nrQg2W���h:W~Y

- **�r**: ��W_�
- **Rr**: 2L-n�
- **�r**: *@Kn�
- **dr**: E�WfD��

## API ���ݤ��

### #;API
- `GET /production/ajax/plan/list/` - #; �֗
- `POST /production/ajax/plan/create/` - #;\
- `GET /production/ajax/plan/<uuid:pk>/detail/` - #;s0֗
- `DELETE /production/ajax/plan/<uuid:pk>/delete/` - #;Jd

### CSV������API
- `POST /production/csv-upload/` - CSVա�������

## �z�1

### ƹ��ՋzTDD	
,_�o TDDTest-Driven Development	�����g�zU�fD~Y

1. **Red Phase**: 1WY�ƹȒ\
2. **Green Phase**: ƹȒY Pn��
3. **Refactor Phase**: ���n��


### ƹȟL��
```bash
# Docker��gn�L
docker exec open_mes python manage.py test production.tests

# y�nƹȯ�n�L
docker exec open_mes python manage.py test production.tests.KaizenModelTest
```

### �X��
- Django 5.1.7
- PostgreSQL
- uuid6 (UUIDv7��)
- django-environ

## ������ƣ�

### CSV�����ɨ��
1. **ա��b���**
   - CSVա��L UTF-8 ���ǣ�gB�Sh���
   - ����LLcWDbgB�Sh���

2. **��b���**
   - ��oYYYY/MM/DD HH:MMbge�
   - zn4oz�Wge�

3. **�������**
   - p�գ���op$ne���
   - �գ���ozkWjD

### 9��H_����
1. **)P���**
   - ��������kij)PL�U�fD�Sh���

2. **���������**
   - ޤ������LcWO�LU�fD�Sh���

## ʌn�5��

1. **����_�**
   - 9���nq����
   - �%9��H�

2. **�_�**
   - 9��Hn�����	��
   - P����_�

3. **�Ф���**
   - ����թ�gn9��H{2
   - �4gn2W��_�

4. **AI#:**
   - 9��Hn���
   - ^<9���n�h

---

Sn_�k�Y��O�а1Jo�z���~gJOD�[O`UD