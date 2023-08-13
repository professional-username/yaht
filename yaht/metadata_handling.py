#!/usr/bin/env python3


def encode_metadata(metadata):
    """Encode a value into a string"""
    datatype = type(metadata)

    # Encode the metadata given its datatype
    if datatype == str:
        return encode_string(metadata)
    elif datatype == list:
        return encode_list(metadata)

    raise NotImplementedError("Datatype %s not supported" % datatype)


def encode_string(metadata):
    return "STRING:%s" % metadata


def encode_list(metadata):
    return "LIST:%s" % ",".join(map(str, metadata))


def extract_metadata(metadata):
    """Extract a value from a string"""
    datatype = metadata.split(":")[0]
    metadata = metadata.split(":")[1]

    # Decode the metadata given its datatype
    if datatype == "STRING":
        return extract_string(metadata)
    elif datatype == "LIST":
        return extract_list(metadata)

    raise NotImplementedError("Datatype %s not supported" % datatype)


def extract_string(metadata):
    return metadata


def extract_list(metadata):
    return metadata.split(",")
