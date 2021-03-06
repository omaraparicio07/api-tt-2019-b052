
from pprint import pprint
from collections import Counter
class Relational():
  """
  Clase que implementa la obtención de sentencias SQL a partir de un diagrama ER generado por
  el proyecto: https://github.com/martinez-acosta/TT-2019-B052.git
  """
  unary_links = []

  def __init__(self,diagram, greet):
    self.diagram = diagram
    self.greet = greet
    self.entity_keys = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] == 'entity']
    self.weak_entity_keys = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] == 'weakEntity']
    self.relation_keys = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] == 'relation']
    self.weak_relation_keys = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] == 'weakRelation']
    self.attrs_keys = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] in ['attribute', 'derivedAttribute', 'keyAttribute', 'multivalueAttribute']]


  def getSentencesSQL(self, project_name, entitiesWithAttrs, relations_NM_to_table_with_attr):
    database_template = """
  DROP DATABASE if exists `{db_name}`;
  CREATE DATABASE `{db_name}`;
  USE `{db_name}`;
  """

    script_sentences = database_template.format(db_name=project_name)

    for table in entitiesWithAttrs:
      # get name table in dict with next(iter(table))
      script_sentences += self.build_table_sentence(table)

    for table in relations_NM_to_table_with_attr:
      # get name table in dict with next(iter(table))
      script_sentences += self.build_table_nm_sentence(table)

    return script_sentences

  def build_table_sentence(self, table_dict):

    table_template = """
  DROP TABLE IF EXISTS `{table_name}`;
  CREATE TABLE IF NOT EXISTS `{table_name}` (
  {attrs_sentences},
  {primary_key}
  {foreing_keys}
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  """
    attr_by_table = ""
    primarykey = table_dict.get('primary_key')
    attr_list = table_dict.get('attributes')
    foreingKeys = table_dict.get('foreing_keys')
    table_name = table_dict['entity'][0].replace(" ", "_")
    foreing_keys=""
    primary_key=""
    for table in table_dict:
      attr_by_table = self.build_columns_sentences(attr_list)
      primary_key = self.buildPrimaryKey(primarykey)
      if foreingKeys:
        primary_key += ","
        foreing_keys = self.buildForeingKeys(foreingKeys)

    return table_template.format(table_name=table_name, attrs_sentences=attr_by_table, primary_key=primary_key, foreing_keys=foreing_keys)

  def build_table_nm_sentence(self, table_dict):

    table_template = """
  ---------------- CREATE TABLE NM relationship----------------
  DROP TABLE IF EXISTS `{table_name}`;
  CREATE TABLE IF NOT EXISTS `{table_name}` (
  {attrs_sentences},
  {primary_key}
  {foreing_keys}
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  """
    attr_by_table = ""
    attr_primarykey_list = table_dict.get('primary_keys')
    attr_relation_list = table_dict.get('attr_relationship')
    foreingKeys_list = table_dict.get('foreing_keys')
    table_name = table_dict['entity'][0].replace(" ", "_")
    foreing_keys=""
    primary_key=""

    for table in table_dict:
      attr_by_table = self.build_columns_nm(attr_primarykey_list)
      if attr_relation_list:
        attr_by_table += ",\n"
        attr_by_table += self.build_columns_sentences(attr_relation_list)
      primary_key = "PRIMARY KEY ({})".format(",".join([f"`{attr[0]}`" for attr in attr_primarykey_list]))
      if foreingKeys_list:
        primary_key += ","
        foreing_keys = self.buildForeingKeysNM(attr_primarykey_list)

    return table_template.format(table_name=table_name, attrs_sentences=attr_by_table, primary_key=primary_key, foreing_keys=foreing_keys)

  def buildPrimaryKey(self, attr_list):
    primary_key_sentence = "PRIMARY KEY ({})"
    primary_key = [f"`{attr[0]}`" for attr in attr_list ]
    return primary_key_sentence.format(",".join(primary_key))

  def buildForeingKeys(self, attr_list):
    foreing_key_sentence = "FOREIGN KEY ({attr_name}) REFERENCES {ref_table_name} ({attr_ref_table})"
    fk_list = []
    for attr in attr_list:
      attr_ref_table, ref_table = attr.rsplit("_",1)
      fk_list.append(f"FOREIGN KEY ({attr}) REFERENCES {ref_table} ({attr_ref_table})")
    return ",\n".join(fk_list)
  
  def buildForeingKeysNM(self, attr_list):
    foreing_key_sentence = "FOREIGN KEY ({attr_name}) REFERENCES {ref_table_name} ({attr_ref_table})"
    fk_list = []
    for attr in attr_list:
      attr_ref_table, ref_table = attr[0].rsplit("_",1)
      fk_list.append(f"FOREIGN KEY ({attr[0]}) REFERENCES {ref_table} ({attr_ref_table})")
    return ",\n".join(fk_list)

  def build_columns_sentences(self, attr_list):

    column_template= "{name} {dt}{dt_s} {not_null} {auto_increment}"
    columns_script = []
    for column in attr_list:
      attrName = column[0].replace(" ", "_")
      dataType = column[3]
      dataSize = column[4]
      notNull = column[5]
      autoIncrement = column[6]
      columns_script.append(column_template.format(name=f"`{attrName}`", dt=dataType, dt_s=f"({dataSize})", not_null=notNull, auto_increment=autoIncrement).rstrip())

    return ",\n".join(columns_script)

  def build_columns_nm(self, attr_list):

    column_template= "{name} {dt}{dt_s} {not_null} {auto_increment}"
    columns_script = []
    for column in attr_list:
      attr_name = column[0].replace(" ", "_")
      dataType = column[3]
      dataSize = column[4]
      notNull = column[5]
      autoIncrement = column[6]
      columns_script.append(column_template.format(name=f"`{attr_name}`", dt=dataType, dt_s=f"({dataSize})", not_null=notNull, auto_increment=autoIncrement).rstrip())

    return ",\n".join(columns_script)

  def getEntities(self, diagram, entity_type='entity'):
    entities = []
    for node in diagram['nodeDataArray']:
      if node['type'] == entity_type:
        entities.append(
          (node['text'].replace(" ", "_"), node['key'])
          )
    return entities

  def getAttrs(self, diagram, multivalue=False):
    attr_types =  ['multivalueAttribute'] if multivalue else ['attribute', 'keyAttribute']
    attrs = []
    for node in diagram['nodeDataArray']:
      if node['type'] in attr_types:
        attrs.append(
          (
            node['text'].replace(" ", "_"),
            node['key'],
            node['type'],
            node['dataType'],
            node['dataSize'] if 'dataSize' in node else 1,
            'NOT NULL' if 'notNull' in node and node['notNull'] else '',
            'AUTO_INCREMENT' if 'autoIncrement' in node and node['dataType'] in ['int', 'bigint'] else '',
          )
        ) 
    return attrs

  def getRelationships(self, diagram):
    relationships = []
    for node in diagram['nodeDataArray']:
      if node['type'] in ['relation', 'weakRelation']:
        relationships.append(
          (node['text'].replace(" ", "_"), node['key'])
          )
    return relationships
  
  def getWeakRelations(self, diagram):
    relationships = []
    for node in diagram['nodeDataArray']:
      if node['type'] in ['weakRelation']:
        relationships.append(
          (node['text'].replace(" ", "_"), node['key'])
          )
    return relationships

  def validateOnlyBinarieRelationship(self, relation, links, entities):
    count = 0
    type_relation = ""
    for node in links:
      if node['from'] == relation[1] and [entity for entity in entities if entity[1] == node['to']]:
        count += 1
      if node['to'] == relation[1] and [entity for entity in entities if entity[1] == node['from']]:
        count += 1
        
    if count == 1:
      type_relation = f"La relación {relation[0]} es de grado 1, el grado mínimo permitido es 2"
    if count >= 3:
      type_relation = f"La relación {relation[0]} es de grado 3 o superior, el grado máximo permitido es 2"
    return type_relation


  def getEntityWithAtributes(self, diagram, entity, attrs):
    diagramDict = diagram
    entityWithAttr = []
    # remove unary links to find unconnected items
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    for node in links_without_unary_link:  #pattern matching from & to
      if node['from'] == entity[1]:
        for attr in attrs:
          if attr[1] == node['to']:
            entityWithAttr.append(attr)
      if node['to'] == entity[1]:
        for attr in attrs:
          if attr[1] == node['from']:
            entityWithAttr.append(attr)
    primary_key = self.validateKeyAttibute({ entity : entityWithAttr })

    return { 'entity' : entity, 'attributes':entityWithAttr, 'primary_key': primary_key, 'foreing_keys':[] }

  def getRelationsNM(self, diagram, relationship):
    attr_nm_relation = []
    diagramDict = diagram
    # remove unary links to find unconnected items
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    for node in links_without_unary_link:
      if ('cardinality' in node ) and (node['cardinality']):
        if node['cardinality'] in ['N','M']:
          if node['to'] == relationship[1]:
            attr_nm_relation.append(node['from'])
          if node['from'] == relationship[1]:
            attr_nm_relation.append(node['to'])
    return {relationship :  attr_nm_relation} if len(attr_nm_relation) == 2 else None

  def getRelations1M(self, diagram, relationship):
    """
    Función para obtener las relaciones 1 a muchos del diagrama entidad relación
    """
    attr_nm_relation = []
    diagramDict = diagram
    # remove unary links to find unconnected items
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    for node in diagramDict['linkDataArray']:
      if ('cardinality' in node ) and (node['cardinality']):
        if node['cardinality'] in ['1','N']:
          if node['to'] == relationship[1] :
            attr_nm_relation.append((node['from'], node['cardinality']))
          if node['from'] == relationship[1] :
            attr_nm_relation.append((node['to'], node['cardinality']))
    return {relationship :  attr_nm_relation} if len(attr_nm_relation) == 2 and attr_nm_relation[0][1] != attr_nm_relation[1][1] else None

  def getRelations11(self, diagram, relationship):
    """
    Función para obtener las relaciones 1 a 1 del diagrama entidad relación
    """
    attr_nm_relation = []
    diagramDict = diagram
    # remove unary links to find unconnected items
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    for node in links_without_unary_link:
      if ('cardinality' in node ) and (node['cardinality']):
        if node['cardinality'] == '1':
          if node['to'] == relationship[1] :
            attr_nm_relation.append((node['from'], node['cardinality']))
          if node['from'] == relationship[1] :
            attr_nm_relation.append((node['to'], node['cardinality']))
    return {relationship :  attr_nm_relation} if len(attr_nm_relation) == 2 else None

  def setForeingKey(self, relations_1N_cardinality, entitiesWithAttrs):

    table_ref = ""
    attr_fk = ""
    table_fk = ""
    pk_ref = ()
    for key in next(iter(relations_1N_cardinality.values())):
      attributes_entity =  [entity for entity in entitiesWithAttrs if entity['entity'][1] == key[0]].pop()
      if key[1] == '1':
        pk_ref = attributes_entity['primary_key'][0]
        ref_table = attributes_entity['entity']
        table_ref = ref_table[0]
        attr_fk = f"{pk_ref[0]}_{ref_table[0].lower()}"
        attr_tuple = list(pk_ref)
        attr_tuple[0] = attr_fk
        pk_ref = tuple(attr_tuple)
      if key[1] == 'N':
        table_fk = [ entity for entity in entitiesWithAttrs if entity['entity'][1] == key[0]].pop()
        ref_table = table_fk['entity']
        table_fk = attributes_entity
    # obtenemos el indice del diccionario de la entidad a modificar
    index_entity = next(i for i,item in enumerate(entitiesWithAttrs) if item == table_fk)
    # agregamos el atributo a la lista de atributos de la entidad
    entitiesWithAttrs[index_entity]['attributes'].append(pk_ref)
    # agregamos el atributo a las llaves foraneas de la entidad
    entitiesWithAttrs[index_entity]['foreing_keys'].append(attr_fk)
    
    return None

  def setForeingKey11(self, relations_1_1_cardinality, entitiesWithAttrs):

    l_table, r_table = next(iter(relations_1_1_cardinality.values()))
    # obtenemos las entidades de la relacion con sus atributos
    attributes_l_entity =  [entity for entity in entitiesWithAttrs if next(iter(entity))[1] == l_table[0]]
    attributes_r_entity =  [entity for entity in entitiesWithAttrs if next(iter(entity))[1] == r_table[0]]
    ## obtener la llave primararia de la tabla 'izquierda'
    pk_l_entity = next(iter(attributes_l_entity[0].values()))['primary_key'][0]
    #formamos la llave forarea con la pk de la tabal izquierda concatenando el nombre de la entidad
    ref_table = next(iter(attributes_l_entity[0]))
    attr_fk = f"{pk_l_entity[0]}_{ref_table[0].lower()}"
    pk_l = list(pk_l_entity)
    pk_l[0] = attr_fk
    pk_l_entity = tuple(pk_l)

    # recuperamos el indice de la tabla 'R' a modificar 
    index_entity = next(i for i,item in enumerate(entitiesWithAttrs) if item == attributes_r_entity[0])

    #Agregamos el atributo a la tabla R
    next(iter(entitiesWithAttrs[index_entity].values()))['attributes'].append((attr_fk, 0, 'fk_attribute', pk_l[3], pk_l[4], pk_l[5], pk_l[6]))
    # next(iter(entitiesWithAttrs[index_entity].values()))['attributes'].append(pk_l)
    # agregamos el atributo a las llaves foraneas de la entidad de la tabla R
    next(iter(entitiesWithAttrs[index_entity].values()))['foreing_keys'].append(attr_fk)

  def validateKeyAttibute(self, entity_with_attrs):
    attrs = next(iter(entity_with_attrs.values())) # get attributes in entinty_with_attr dictionary
    primary_key = [attr for attr in attrs if attr[2] == 'keyAttribute']
    
    return primary_key

  def greeting(self):
    return f"Saludos desde la clase relacional.py {self.greet}"

  def getAttrsNMRelation(self, diagram, entitiesWithAttrs, relation_nm, attrs):
    attr_nm_relation = []
    primary_keys = []
    foreing_keys = []
    table_name = next(iter(relation_nm))[0]
    for entity_attrs in entitiesWithAttrs:
      if entity_attrs['entity'][1] in next(iter(relation_nm.values())):
        primary_key = entity_attrs['primary_key'][0]
        ref_table = entity_attrs['entity']
        attr_fk = f"{primary_key[0]}_{ref_table[0].lower()}"
        attr_tuple = list(primary_key)
        attr_tuple[0] = attr_fk
        table_name += "_"+ref_table[0].lower()
        primary_key = tuple(attr_tuple)
        primary_keys.append(primary_key)
        foreing_keys.append(attr_fk)
    attr_nm_relation = [self.getEntityWithAtributes(diagram, next(iter(relation_nm)), attrs)]
    return {'entity' : (table_name, next(iter(relation_nm))[1] ),
            "primary_keys":primary_keys,
            "foreing_keys" : foreing_keys,
            "attr_relationship": attr_nm_relation[0]['attributes']
            }
  
  def convertAttrMultivalueToEntity(self, attr_multivalue, entitiesWithAttrs):
    """
    Método para convetir un atributo multivalor en una entidad, paso 6 de la transformación a sentencias SQL
    """
    links = [ link for link in self.diagram['linkDataArray'] if not link in self.unary_links ]
    for link in links:
      if link['to'] == attr_multivalue[1]:
        e = [entity for entity in entitiesWithAttrs if entity['entity'][1] == link['from']]
      if link['from'] == attr_multivalue[1]:
        e = [entity for entity in entitiesWithAttrs if entity['entity'][1] == link['to']]

    pk_e = e[0].get('primary_key')
    entity = e[0].get('entity')
    pk_tuple=list(pk_e[0])
    pk_tuple[0] = f"{pk_e[0][0]}_{entity[0]}".lower()
    table_name = f"{attr_multivalue[0]}_{entity[0]}"
    table = { 'entity':(table_name.lower() , attr_multivalue[1]),
              "primary_key":[attr_multivalue, tuple(pk_tuple)],
              "foreing_keys" : [f"{pk_e[0][0]}_{entity[0]}".lower()],
              "attributes": [attr_multivalue, tuple(pk_tuple)]
            }
    return table

  def convertToSQLSenteneces(self, diagram, db_name):
    
    entities = self.getEntities(diagram)
    attrs = self.getAttrs(diagram)
    attr_multivalue = self.getAttrs(diagram, True)
    unary_links = self.getUniryLink(diagram['linkDataArray'])
    entitiesWithAttrs = [self.getEntityWithAtributes(diagram, entity, attrs) for entity in entities]
    entitiesWithAttrs += [self.convertAttrMultivalueToEntity(attr, entitiesWithAttrs) for attr in attr_multivalue]
    relations = self.getRelationships(diagram)
    relations_NM_to_table = [self.getRelationsNM(diagram, relationship ) for relationship in relations]
    relations_NM_to_table = [ i for i in relations_NM_to_table if i] #remove empty items
    relations_NM_to_table_with_attr = [self.getAttrsNMRelation(diagram, entitiesWithAttrs, relation_nm, attrs) for  relation_nm in relations_NM_to_table]
    relations_1M = [self.getRelations1M(diagram, relationship ) for relationship in relations]
    relations_1M = [ i for i in relations_1M if i]
    relations_1_1 = [self.getRelations11(diagram, relationship ) for relationship in relations]
    relations_1_1 = [i for i in relations_1_1 if i]

    if relations_1M :
      for r in relations_1M:
        self.setForeingKey(r, entitiesWithAttrs) 
    if relations_1_1 :
      for r in relations_1_1:
        self.setForeingKey11(r, entitiesWithAttrs)

    lOrde =  sorted(entitiesWithAttrs, key=lambda k: len(k['foreing_keys'])) 
    return self.getSentencesSQL(db_name, lOrde , relations_NM_to_table_with_attr)

  def validateDiagramStructure(self, diagram):
    errors = {}
    general_errors = self.generalValidations(diagram)
    relations_errors = self.realtionsValidations(diagram)
    entities_errors = self.entitiesValidations(diagram)
    attrs_errors = self.attrsValidations(diagram)
    if general_errors : errors['general_errors'] = general_errors
    if entities_errors : errors['entities_errors'] = entities_errors
    if attrs_errors : errors['attrs_errors'] = attrs_errors
    if relations_errors : errors['relations_errors'] = relations_errors
    return errors

  def generalValidations(self, diagram):
    general_errors = []
    unary_links = self.getUniryLink(diagram['linkDataArray'])
    unconnected_items = self.getUnconnectedItems(diagram)
    duplicated_names = self.getDuplicatedNames(diagram['nodeDataArray'])
    if unary_links: general_errors += unary_links
    if unconnected_items: general_errors += unconnected_items
    if duplicated_names: general_errors += duplicated_names
    return general_errors

  def entitiesValidations(self, diagram):
    entities_errors = []
    entities = self.getEntities(diagram)
    weak_entities = self.getEntities(diagram, 'weakEntity')
    attrs = self.getAttrs(diagram)
    entities_with_attrs = [self.getEntityWithAtributes(diagram, entity, attrs) for entity in entities + weak_entities ]
    entities_errors = self.getEntitiesWithoutAttrsOrPk(entities, attrs, entities_with_attrs )
    connection_between_entities = self.getConnectionsBetweenEntitites(diagram)
    weakE_participation = self.getWeakEntitiesParticipations(diagram, entities)

    return entities_errors + connection_between_entities + weakE_participation

  def getUniryLink(self, link_data_array):
    unary_links_list = []
    for link in link_data_array:
      if not all (k in link for k in ['from', 'to']) :
        unary_links_list.append(f"Enlace sin conexión , {link}")
        self.unary_links.append(link)
        
    return unary_links_list

  def getDuplicatedNames(self, nodos):
    names_list = [node['text'] for node in nodos if node['type'] in ['entity', 'weakEntity'] ]
    duplicated_names = [ (name, count) for name, count in Counter(names_list).items() if count > 1 ]
    duplicated_names = [f"Se encontraron {dn[1]} elementos con el nombre {dn[0]}, no debe haber elementos con el mismo nombre." for dn in duplicated_names]
    return duplicated_names
  
  def getUnconnectedItems(self, diagram):
    unconnected_list = []
    keys_list = [ (item['key'], item['text']) for item in diagram['nodeDataArray']]
    # remove unary links to find unconnected items
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]

    for key in keys_list:
      item_with_conexions = [item for item in links_without_unary_link if item['from'] == key[0] or item['to'] == key[0] ]
      if not item_with_conexions: unconnected_list.append(f"El elemento {key[1]} no cuenta con conexiones.")

    return unconnected_list 
        
  def getEntitiesWithoutAttrsOrPk(self, entities, attrs, entities_with_attrs):

    entities_without_attr = []
    entities_without_pk = []
    for entity_with_attr in entities_with_attrs:
      # entity_with_attr = next(iter(entity_with_attr.values()))
      if not entity_with_attr['attributes']:
        entity_without_attrs = next(iter(entity_with_attr.keys()))
        entities_without_attr.append(f"La entidad {entity_without_attrs[0]} no cuenta con atributos.")
      if not entity_with_attr['primary_key']:
        entity_without_pk = next(iter(entity_with_attr.keys()))
        entities_without_pk.append(f"La entidad {entity_without_pk[0]} no cuenta con un atributo clave.")

    return entities_without_attr + entities_without_pk

  def getConnectionsBetweenEntitites(self, diagram):
    conn_bt_entities = []
    entities_keys_list = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] in ['entity', 'weakEntity'] ]
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    for link in links_without_unary_link:
      if link['from'] in entities_keys_list and link['to'] in entities_keys_list :
        entity_a = [ item['text'] for item in diagram['nodeDataArray'] if item['key'] == link['from'] ]
        entity_b = [ item['text'] for item in diagram['nodeDataArray'] if item['key'] == link['to'] ]
        conn_bt_entities.append(f"No esta permitida la conexión directa entre entidades, {entity_a[0]} <=> {entity_b[0]}.")

    return conn_bt_entities
  
  def getConnectionsMoreOneRelations(self, diagram, entity):
    conn_relationships = 0
    rel_keys = []
    relations_keys_list = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] in ['relation', 'weakRelation'] ]
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    for link in links_without_unary_link:
      if link['from'] == entity[1] and link['to'] in relations_keys_list:
        conn_relationships +=1
        rel_keys.append(link['to'])
      if link['to'] == entity[1] and link['from'] in relations_keys_list:
        conn_relationships +=1
        rel_keys.append(link['from'])

    return True if conn_relationships>1 and rel_keys[0] != rel_keys[1] else False
  
  def getWeakEntitiesParticipations(self, diagram, entities):
    rel_keys = []
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    weakE_keys_list = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] in [ 'weakEntity'] ]
    weakR_keys_list = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] in ['weakRelation']]
    for link in links_without_unary_link:
      if link['from'] in weakE_keys_list and link['to'] in weakR_keys_list:
        if 'participacion' in link and link['participacion'] == 'parcial':
          rel_keys.append(f"La entidad {link['from']} no puede existir por participación parcial.")
      if link['to'] in weakE_keys_list and link['from'] in weakR_keys_list :
        if 'participacion' in link and link['participacion'] == 'parcial':
          rel_keys.append(f"La entidad {link['to']} no puede existir por participación parcial.")
      if link['from'] in weakE_keys_list and not link['to'] in weakR_keys_list:
        rel_keys.append(f"La entidad {link['from']} solo puede conectarse a una relación de tipo débil.")
      if link['to'] in weakE_keys_list and not link['from'] in weakR_keys_list:
        rel_keys.append(f"La entidad {link['to']} solo puede conectarse a una relación de tipo débil.")

    return rel_keys

  def attrsValidations(self, diagram):
    errors_attr = []
    entities_keys_list = [ item['key'] for item in diagram['nodeDataArray'] if item['type'] in ['entity', 'weakEntity', 'relation', 'weakRelation'] ]
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    attrs = self.getAttrs(diagram)
    # atributos conectados a las de un elemento(excepto si es del tipo compuesto)
    attr_multi_conn = [attr[0] for attr in attrs if self.getAttrMultiConnections(attr, links_without_unary_link) ]
    attr_multi_conn = [f"El atributo {attr} se encuentra conectado a mas de una elemento." for attr in attr_multi_conn]
    # atributos compuesto o derivados conectados a otro elemento que no sea una entidad
    attrs_no_conn_entity = [attr[0] for attr in attrs if self.getAttrsNotEntityConnected(attr, links_without_unary_link, entities_keys_list) ]
    attrs_no_conn_entity = [f"El atributo {attr} solo puede conectarse a una entidad." for attr in attrs_no_conn_entity]

    return attr_multi_conn + attrs_no_conn_entity

  def getAttrMultiConnections(self, attr, links):
    count = 0
    for link in links:
      if link['to'] == attr[1] or link['from'] == attr[1]:
        count = count + 1
    return False if count <= 1 else True

  def getAttrsNotEntityConnected(self, attr, links, entity_keys):
    entity_connected = False
    for link in links:
      if attr[1] == link['to'] and not link['from'] in entity_keys:
        entity_connected = True
        break;
      if attr[1] == link['from'] and not link['to'] in entity_keys:
        entity_connected = True
        break;
    return entity_connected

  def realtionsValidations(self, diagram):
    relations = self.getRelationships(diagram)
    weak_relations = self.getWeakRelations(diagram)
    entities = self.getEntities(diagram)
    weak_entities = self.getEntities(diagram,'weakEntity')
    links_without_unary_link = [ link for link in diagram['linkDataArray'] if not link in self.unary_links ]
    relation_no_binary = [ self.validateOnlyBinarieRelationship(relation, links_without_unary_link, entities + weak_entities) for relation in relations]
    relation_no_binary = [ relation for relation in relation_no_binary if relation]
    card_errors = [rel for rel in relations if self.getRelationWithoutCardinality(rel, links_without_unary_link) ]
    card_errors = [f"La relación {r[0]} no tiene una cardinalidad valida, debe ser 1, N ó M." for r in card_errors ]
    part_errors = [rel for rel in relations if self.getRelationWithoutParticipation(rel, links_without_unary_link) ]
    part_errors = [f"La relación {r[0]} no tiene un tipo de participación, debe ser total o parcial." for r in part_errors ]
    weak_rel_error = [ self.validateWeakRelationConnections(relation, links_without_unary_link) for relation in weak_relations]

    return relation_no_binary + card_errors + part_errors + weak_rel_error

  def getRelationWithoutCardinality(self, relation, links):
    cardinality_invalid = False
    for link in links:
      if link['to'] == relation[1] and not link['from'] in self.attrs_keys:
        if not 'cardinality' in link or not link['cardinality'] in ['1','N', 'M'] :
          cardinality_invalid = True
      if link['from'] == relation[1] and not link['to'] in self.attrs_keys:
        if not 'cardinality' in link or not link['cardinality'] in ['1','N', 'M'] :
          cardinality_invalid = True
    return cardinality_invalid
  
  def getRelationWithoutParticipation(self, relation, links):
    participation_valid = False
    for link in links:
      if link['to'] == relation[1] and not link['from'] in self.attrs_keys:
        if not 'participacion' in link:
          participation_valid = True
      if link['from'] == relation[1] and not link['to'] in self.attrs_keys:
        if not 'participacion' in link:
          participation_valid = True
    return participation_valid

  def validateWeakRelationConnections(self, relation, links):
    type_relation = ""
    string_rel = ""
    for node in links:
      if node['from'] == relation[1]:
        if node['to'] in self.weak_entity_keys: string_rel += "w" # weak entity
        if node['to'] in self.entity_keys: string_rel += "s" #strong entity
      if node['to'] == relation[1]:
        if node['from'] in self.weak_entity_keys: string_rel += "w" # weak entity
        if node['from'] in self.entity_keys: string_rel += "s" #strong entity

    if not string_rel in ['ws', 'sw']:
      type_relation = f"La relación {relation[0]} solo puede existir entre una entidad débil y una entidad fuerte."
    return type_relation